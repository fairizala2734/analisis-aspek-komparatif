"""Conservative deterministic fallback used only as a safety net."""

import re
from collections.abc import Callable


def candidate_prefilter(code: str, normalize: Callable[[str], str]) -> str:
    """Preserve the legacy fallback mapping for behavior compatibility."""

    candidate = normalize(code)
    candidate = re.sub(r"\b(batik tulis|batik cap)\b", "", candidate).strip()
    candidate = re.sub(r"\s+", " ", candidate).strip(" -_/.,")
    natural = {
        "buat": "pembuatan",
        "gores": "goresan",
        "unggul": "keunggulan",
        "unik": "keunikan",
        "eksklusif": "eksklusivitas",
        "mewah": "kemewahan",
        "beragam": "keragaman",
        "awet": "daya tahan",
        "tahan lama": "daya tahan",
    }
    return natural.get(candidate, candidate)
