"""LLM-backed comparative question validator."""

from __future__ import annotations

from pathlib import Path

from llm.client import LLMClient
from llm.prompts.comparative_validation import COMPARATIVE_VALIDATION_SYSTEM_PROMPT


class ComparativeQuestionJudger:
    def __init__(
        self,
        client: LLMClient,
        *,
        retry_per_call: int,
        always_retry: bool,
        raw_log_path: Path | None = None,
        log_fn=None,
        update_timer_fn=None,
    ) -> None:
        self.client = client
        self.retry_per_call = retry_per_call
        self.always_retry = always_retry
        self.raw_log_path = raw_log_path
        self.log_fn = log_fn
        self.update_timer_fn = update_timer_fn

    def set_raw_log_path(self, raw_log_path: Path | None) -> None:
        self.raw_log_path = raw_log_path

    def __call__(
        self,
        row_id: int,
        question: str,
        matched_entities: list[str],
    ) -> tuple[bool, str]:
        if self.log_fn:
            self.log_fn(
                f"Row {row_id}: entity cocok ({' | '.join(matched_entities)}); "
                "meminta LLM menilai bentuk pertanyaan komparatif."
            )
        payload = {
            "row_id": row_id,
            "question": question,
            "matched_entities": matched_entities,
        }
        result = self.client.call_json(
            COMPARATIVE_VALIDATION_SYSTEM_PROMPT,
            payload,
            retry_per_call=self.retry_per_call,
            always_retry=self.always_retry,
            raw_log_path=self.raw_log_path,
            log_fn=self.log_fn,
            update_timer_fn=self.update_timer_fn,
        )
        is_comparative = bool(result.get("is_comparative"))
        reason = str(result.get("reason", "") or "").strip()
        if not reason:
            reason = (
                "Lolos validasi komparatif."
                if is_comparative
                else "LLM menilai pertanyaan ini tidak komparatif."
            )
        if self.log_fn:
            status = "komparatif" if is_comparative else "tidak komparatif"
            self.log_fn(f"Row {row_id}: hasil pemeriksaan LLM = {status}. Alasan: {reason}")
        return is_comparative, reason
