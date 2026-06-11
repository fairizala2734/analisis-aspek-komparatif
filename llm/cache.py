"""Content-addressed LLM response cache."""

import hashlib
import json
from pathlib import Path
from typing import Any


def call_hash(system_prompt: str, user_payload: dict[str, Any], model: str) -> str:
    canonical = json.dumps(
        {
            "system_prompt": system_prompt,
            "user_payload": user_payload,
            "model": model,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class LLMCallCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir

    def _path(self, key: str) -> Path:
        return self.cache_dir / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else None
        except Exception:
            return None

    def put(self, key: str, value: dict[str, Any]) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
