"""Deterministic LLM implementation for unit and smoke tests."""

from collections.abc import Callable
from pathlib import Path
from typing import Any


class MockLLM:
    """Return fixture responses based on the input payload shape."""

    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    def call_json(
        self,
        system_prompt: str,
        user_payload: dict[str, Any],
        *,
        retry_per_call: int = 0,
        always_retry: bool = False,
        raw_log_path: Path | None = None,
        log_fn: Callable[[str], None] | None = None,
        update_timer_fn: Callable[[], None] | None = None,
    ) -> dict[str, Any]:
        del retry_per_call, always_retry, raw_log_path, update_timer_fn
        self.calls.append({"prompt": system_prompt, "payload": user_payload})
        if log_fn:
            log_fn("MockLLM deterministic response.")

        if "items" in user_payload and "total_unique_candidate_codes" in user_payload:
            return {
                "generic_heads_detected": [],
                "reviewed_count": int(user_payload["total_unique_candidate_codes"]),
                "items": [],
            }
        if "opinion_unit" in user_payload:
            return {
                "candidate_code": "aspek",
                "main_position": str(user_payload.get("main_opinion", "")),
                "counterpart_position": str(user_payload.get("counterpart_opinion", "")),
                "candidate_reason": "Fixture deterministik.",
                "confidence": "high",
            }
        answer = str(user_payload.get("answer", "")).strip()
        return {
            "answer_cleaned": answer,
            "items": [
                {
                    "opinion_unit": answer,
                    "main_entity": "objek a",
                    "main_opinion": answer,
                    "main_sentiment": "neutral",
                    "main_source": "explicit",
                    "main_evidence_text": answer,
                    "counterpart_entity": "objek b",
                    "counterpart_opinion": "",
                    "counterpart_sentiment": "neutral",
                    "counterpart_source": "none",
                    "counterpart_evidence_text": "",
                    "counterpart_logic": "not_available",
                    "confidence": "high",
                }
            ]
            if answer
            else [],
        }
