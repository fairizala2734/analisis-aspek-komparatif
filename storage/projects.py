"""Project directories, manifests, signatures, and ZIP exports."""

import hashlib
import io
import json
import re
import unicodedata
import zipfile
from pathlib import Path
from typing import Any

from llm.prompts.registry import prompt_hashes
from pipeline.config import APP_VERSION

OUTPUT_FILES = [
    "01_entity_validation.csv",
    "01_raw_dataset.csv",
    "02_opinion_units.csv",
    "02c_opinion_units_pos.csv",
    "02c_pos_errors.csv",
    "03_candidate_codes.csv",
    "03_candidate_errors.csv",
    "04_candidate_summary.csv",
    "05_candidate_code_mapping.csv",
    "05_candidate_code_normalized.csv",
    "05_candidate_normalization_errors.csv",
    "06_candidate_summary_normalized.csv",
    "02_errors.csv",
    "manifest.json",
    "raw_llm_responses.jsonl",
    "02_opinion_units_imported_from.txt",
    "cache_import_report.json",
    "manual_candidate_code_edits.jsonl",
]


def dataset_signature(raw_bytes: bytes, settings_for_signature: dict[str, Any]) -> str:
    digest = hashlib.sha256()
    digest.update(raw_bytes)
    digest.update(
        json.dumps(
            settings_for_signature,
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    )
    return digest.hexdigest()[:16]


def _slugify(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:40] or "run"


def get_project_dir(local_results_dir: Path, signature: str, project_title: str = "") -> Path:
    if project_title:
        return local_results_dir / "projects" / f"{_slugify(project_title)}__{signature}"
    return local_results_dir / "projects" / signature


def load_manifest(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "manifest.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def write_manifest(project_dir: Path, manifest: dict[str, Any]) -> None:
    project_dir.mkdir(parents=True, exist_ok=True)
    enriched = {
        **manifest,
        "app_version": APP_VERSION,
        "prompt_hashes": prompt_hashes(),
        "run_id": str(manifest.get("run_id") or manifest.get("signature") or project_dir.name),
        "params": dict(manifest.get("params") or manifest.get("settings") or {}),
    }
    (project_dir / "manifest.json").write_text(
        json.dumps(enriched, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def make_result_zip(project_dir: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename in OUTPUT_FILES:
            path = project_dir / filename
            if path.exists():
                archive.write(path, arcname=filename)
    return buffer.getvalue()
