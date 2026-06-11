"""OpenRouter-compatible LLM client with retry, cache, and raw logging."""

import concurrent.futures
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from openai import OpenAI

from llm.cache import LLMCallCache, call_hash
from llm.json_parser import extract_json_obj

TRANSIENT_ERROR_PATTERNS = (
    "429",
    "500",
    "502",
    "503",
    "504",
    "timeout",
    "timed out",
    "connect timeout",
    "read timeout",
    "connection reset",
    "reset after",
    "rate limit",
    "temporarily unavailable",
    "service unavailable",
    "gateway",
    "bad gateway",
    "upstream",
)


def is_transient_error(exc: Exception) -> bool:
    message = str(exc).lower()
    return any(pattern in message for pattern in TRANSIENT_ERROR_PATTERNS)


@dataclass
class LLMUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    elapsed_seconds: float = 0.0
    cache_hit: bool = False


class LLMClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 4000,
        json_mode: bool = False,
        timeout_seconds: int = 180,
        retry_base_sleep: float = 4.0,
        retry_max_sleep: float = 30.0,
        http_referer: str = "http://localhost:8501",
        app_title: str = "Opinion Unit Extractor",
        cache_dir: Path | None = None,
        read_cache: bool = True,
        write_cache: bool = True,
    ):
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY / llm.api_key belum diisi.")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.json_mode = json_mode
        self.retry_base_sleep = retry_base_sleep
        self.retry_max_sleep = retry_max_sleep
        self.cache = LLMCallCache(cache_dir) if cache_dir else None
        self.read_cache = read_cache
        self.write_cache = write_cache
        self.last_usage = LLMUsage()
        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            timeout=timeout_seconds,
            default_headers={
                "HTTP-Referer": http_referer,
                "X-OpenRouter-Title": app_title,
            },
        )

    def _request(self, system_prompt: str, user_payload: dict[str, Any]) -> tuple[str, LLMUsage]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if self.json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        started = time.perf_counter()
        response = self._client.chat.completions.create(**kwargs)
        elapsed = time.perf_counter() - started
        usage = getattr(response, "usage", None)
        metrics = LLMUsage(
            prompt_tokens=int(getattr(usage, "prompt_tokens", 0) or 0),
            completion_tokens=int(getattr(usage, "completion_tokens", 0) or 0),
            total_tokens=int(getattr(usage, "total_tokens", 0) or 0),
            elapsed_seconds=elapsed,
        )
        return response.choices[0].message.content or "", metrics

    def call_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        *,
        retry_per_call: int,
        always_retry: bool,
        raw_log_path: Path | None = None,
        log_fn: Callable[[str], None] | None = None,
        update_timer_fn: Callable[[], None] | None = None,
    ) -> dict[str, Any]:
        key = call_hash(system_prompt, user_payload, self.model)
        row_id = user_payload.get("row_id", "?")
        if self.cache and self.read_cache:
            cached = self.cache.get(key)
            if cached is not None:
                self.last_usage = LLMUsage(cache_hit=True)
                if log_fn:
                    log_fn(f"Row {row_id}: LLM cache hit {key[:12]}; request OpenRouter dilewati.")
                return cached
        elif self.cache and log_fn:
            log_fn(f"Row {row_id}: cache LLM dilewati; request baru dikirim ke OpenRouter.")

        attempt = 0
        max_manual_attempts = max(0, int(retry_per_call)) + 1
        last_error: Exception | None = None

        while True:
            attempt += 1
            if log_fn:
                log_fn(f"Row {row_id}: kirim request LLM attempt {attempt}...")
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._request, system_prompt, user_payload)
                    while not future.done():
                        if update_timer_fn:
                            update_timer_fn()
                        time.sleep(1.0)
                    raw, usage = future.result()
                self.last_usage = usage

                if raw_log_path:
                    raw_log_path.parent.mkdir(parents=True, exist_ok=True)
                    with raw_log_path.open("a", encoding="utf-8") as file:
                        file.write(
                            json.dumps(
                                {
                                    "ts": datetime.now().isoformat(timespec="seconds"),
                                    "model": self.model,
                                    "attempt": attempt,
                                    "call_hash": key,
                                    "usage": usage.__dict__,
                                    "payload": user_payload,
                                    "raw": raw,
                                },
                                ensure_ascii=False,
                            )
                            + "\n"
                        )

                result = extract_json_obj(raw)
                if self.cache and self.write_cache:
                    self.cache.put(key, result)
                if log_fn:
                    log_fn(f"Row {row_id}: LLM sukses attempt {attempt}.")
                return result
            except Exception as exc:
                last_error = exc
                temporary = is_transient_error(exc)
                if log_fn:
                    error_short = str(exc).replace("\n", " ")[:350]
                    log_fn(
                        f"Row {row_id}: LLM gagal attempt {attempt}. "
                        f"temporary={temporary}. Error: {error_short}"
                    )

                should_retry = (always_retry and temporary) or attempt < max_manual_attempts
                if not should_retry:
                    raise RuntimeError(
                        f"LLM call gagal setelah {attempt} attempt. Error terakhir: {last_error}"
                    ) from exc

                sleep_seconds = min(
                    self.retry_base_sleep * (2 ** min(attempt - 1, 4)),
                    self.retry_max_sleep,
                )
                end_sleep = time.perf_counter() + sleep_seconds
                while time.perf_counter() < end_sleep:
                    if update_timer_fn:
                        update_timer_fn()
                    time.sleep(1.0)
