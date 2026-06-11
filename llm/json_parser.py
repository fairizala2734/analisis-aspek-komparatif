"""Robust JSON-object extraction from model text."""

import json
import re
from typing import Any


def extract_json_obj(text: str) -> dict[str, Any]:
    if not text or not str(text).strip():
        raise ValueError("Response LLM kosong.")

    text = str(text).strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fence:
        try:
            obj = json.loads(fence.group(1))
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        snippet = text[start : end + 1]
        try:
            obj = json.loads(snippet)
            if isinstance(obj, dict):
                return obj
        except Exception as exc:
            raise ValueError(f"Tidak menemukan JSON valid dari response. Error parse: {exc}") from exc

    raise ValueError("Tidak menemukan JSON valid dari response.")
