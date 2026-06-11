import io
import json
import os
import re
import shutil
import time
import zipfile
import hashlib
import traceback
import unicodedata
import concurrent.futures
import threading
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from openai import OpenAI

import storage
from ui import components as ui
from pipeline.config import RUN_UNTIL_OPTIONS, STEP_VERSIONS, load_settings
from pipeline.schemas import (
    CANDIDATE_COLUMNS,
    CANDIDATE_ERROR_COLUMNS,
    ERROR_COLUMNS,
    NORMALIZATION_MAPPING_COLUMNS,
    NORMALIZED_COLUMNS,
    NORMALIZED_SUMMARY_COLUMNS,
    OUTPUT_COLUMNS,
    POS_COLUMNS,
    SUMMARY_COLUMNS,
)
from pipeline.ingest.csv_io import df_to_csv_bytes, load_csv_flexible, safe_read_csv, save_df
from pipeline.ingest.entity_validation import (
    ComparisonEntity,
    canonicalize_entity,
    match_entities,
    parse_comparison_entities,
    validate_entity_setup,
)
from pipeline.ingest.raw_dataset import (
    build_raw_dataset,
    detect_question_answer_columns,
    mechanical_clean_text,
    normalize_raw_dataset,
)
from pipeline.normalization.fallback import candidate_prefilter
from pipeline.normalization.guards import derive_generic_heads_from_data, detect_overmerged_labels
from pipeline.stanza import format_pos_and_nouns, load_stanza_pipeline
from llm.client import LLMClient
from llm.comparative_validator import ComparativeQuestionJudger
from storage.projects import dataset_signature as project_dataset_signature
from storage.projects import get_project_dir as project_dir_for
from storage.projects import load_manifest as project_load_manifest
from storage.projects import make_result_zip as project_make_result_zip
from storage.projects import write_manifest as project_write_manifest
from llm.prompts.candidate_codes import CANDIDATE_CODE_SYSTEM_PROMPT
from llm.prompts.normalization import CANDIDATE_NORMALIZATION_SYSTEM_PROMPT
from llm.prompts.opinion_units import OPINION_UNITS_SYSTEM_PROMPT
from llm.prompts.entity_context import ENTITY_CONTEXT_RULES
from llm.prompts.relabel import RELABEL_SYSTEM_PROMPT
from llm.prompts.registry import prompt_hashes
from ui.entity_input import render_comparison_entity_input

try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx
except Exception:  # pragma: no cover - compatibility across Streamlit versions
    add_script_run_ctx = None


# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="Analisis Aspek Komparatif",
    page_icon=":material/analytics:",
    layout="wide",
)



# ============================================================
# CONFIG HELPERS
# ============================================================

APP_SETTINGS = load_settings(st.secrets)
LLM_BASE_URL = APP_SETTINGS.llm_base_url
LLM_API_KEY = APP_SETTINGS.llm_api_key
LLM_MODEL = APP_SETTINGS.llm_model
LLM_TEMPERATURE = APP_SETTINGS.llm_temperature
LLM_MAX_TOKENS = APP_SETTINGS.llm_max_tokens
LLM_USE_JSON_MODE = APP_SETTINGS.llm_use_json_mode
LLM_RETRY_BASE_SLEEP = APP_SETTINGS.llm_retry_base_sleep
LLM_RETRY_MAX_SLEEP = APP_SETTINGS.llm_retry_max_sleep
LLM_ALWAYS_RETRY_DEFAULT = APP_SETTINGS.llm_always_retry
OPENROUTER_HTTP_REFERER = APP_SETTINGS.openrouter_http_referer
OPENROUTER_APP_TITLE = APP_SETTINGS.openrouter_app_title
LOCAL_RESULTS_DIR = APP_SETTINGS.local_results_dir

OPENROUTER_FREE_MODEL_OPTIONS = {
    "OpenAI gpt-oss-120b (free) - rekomendasi": "openai/gpt-oss-120b:free",
    "OpenAI gpt-oss-20b (free) - lebih ringan": "openai/gpt-oss-20b:free",
    "Google Gemma 4 31B (free)": "google/gemma-4-31b-it:free",
    "Moonshot Kimi K2.6 (free)": "moonshotai/kimi-k2.6:free",
    "OpenRouter Free Router": "openrouter/free",
    "Custom model dari secrets/env": LLM_MODEL,
}








# OpenRouter defaults.
# Isi API key di .streamlit/secrets.toml atau environment variable OPENROUTER_API_KEY.















# ============================================================
# PROMPT
# ============================================================










# ============================================================
# TEXT / CSV HELPERS
# ============================================================
















# ============================================================
# LIVE UI LOG / TIMER HELPERS
# ============================================================

def format_elapsed(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def make_live_logger(log_box=None, timer_box=None, start_time: Optional[float] = None):
    lines: List[str] = []

    def update_timer():
        if timer_box is not None and start_time is not None:
            timer_box.metric("Waktu proses", format_elapsed(time.perf_counter() - start_time))

    def log(message: str):
        update_timer()
        now = datetime.now().strftime("%H:%M:%S")
        elapsed = format_elapsed(time.perf_counter() - start_time) if start_time is not None else "00:00"
        lines.append(f"[{now} | +{elapsed}] {message}")
        # Batasi agar UI tidak berat kalau retry lama.
        del lines[:-200]
        if log_box is not None:
            log_box.code("\n".join(lines), language="text")

    return log, update_timer


def start_timer_watcher(timer_box, start_time: float):
    stop_event = threading.Event()

    def run() -> None:
        while not stop_event.wait(1.0):
            try:
                timer_box.metric("Waktu proses", format_elapsed(time.perf_counter() - start_time))
            except Exception:
                break

    thread = threading.Thread(target=run, daemon=True)
    if add_script_run_ctx is not None:
        try:
            add_script_run_ctx(thread)
        except Exception:
            pass
    timer_box.metric("Waktu proses", "00:00")
    thread.start()
    return stop_event, thread

# ============================================================
# JSON / LLM HELPERS
# ============================================================








def call_llm_json(
    system_prompt: str,
    user_payload: Dict[str, Any],
    *,
    model_id: str,
    timeout_seconds: int,
    retry_per_call: int,
    always_retry_per_call: bool,
    raw_log_path: Optional[Path] = None,
    log_fn=None,
    update_timer_fn=None,
    bypass_cache: bool = False,
) -> Dict[str, Any]:
    client = LLMClient(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        model=model_id,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        json_mode=LLM_USE_JSON_MODE,
        timeout_seconds=timeout_seconds,
        retry_base_sleep=LLM_RETRY_BASE_SLEEP,
        retry_max_sleep=LLM_RETRY_MAX_SLEEP,
        http_referer=OPENROUTER_HTTP_REFERER,
        app_title=OPENROUTER_APP_TITLE,
        cache_dir=LOCAL_RESULTS_DIR / "llm_cache",
        read_cache=not bypass_cache,
    )
    return client.call_json(
        system_prompt,
        user_payload,
        retry_per_call=retry_per_call,
        always_retry=always_retry_per_call,
        raw_log_path=raw_log_path,
        log_fn=log_fn,
        update_timer_fn=update_timer_fn,
    )


def make_comparative_judger(
    *,
    model_id: str,
    timeout_seconds: int,
    retry_per_call: int,
    always_retry_per_call: bool,
    raw_log_path: Optional[Path] = None,
    log_fn=None,
    update_timer_fn=None,
    bypass_cache: bool = False,
) -> ComparativeQuestionJudger:
    client = LLMClient(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        model=model_id,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        json_mode=LLM_USE_JSON_MODE,
        timeout_seconds=timeout_seconds,
        retry_base_sleep=LLM_RETRY_BASE_SLEEP,
        retry_max_sleep=LLM_RETRY_MAX_SLEEP,
        http_referer=OPENROUTER_HTTP_REFERER,
        app_title=OPENROUTER_APP_TITLE,
        cache_dir=LOCAL_RESULTS_DIR / "llm_cache",
        read_cache=not bypass_cache,
    )
    return ComparativeQuestionJudger(
        client,
        retry_per_call=retry_per_call,
        always_retry=always_retry_per_call,
        raw_log_path=raw_log_path,
        log_fn=log_fn,
        update_timer_fn=update_timer_fn,
    )
# ============================================================
# CACHE / PROJECT HELPERS
# ============================================================

def dataset_signature(raw_bytes: bytes, settings_for_signature: Dict[str, Any]) -> str:
    return project_dataset_signature(raw_bytes, settings_for_signature)


def get_project_dir(signature: str, project_title: str = "") -> Path:
    return project_dir_for(LOCAL_RESULTS_DIR, signature, project_title)


def write_manifest(project_dir: Path, manifest: Dict[str, Any]) -> None:
    project_write_manifest(project_dir, manifest)


def load_manifest(project_dir: Path) -> Dict[str, Any]:
    return project_load_manifest(project_dir)


def make_result_zip(project_dir: Path) -> bytes:
    return project_make_result_zip(project_dir)










def _norm_for_cache_compare(value: Any) -> str:
    """Normalize text lightly so compatible cache checks are not broken by whitespace."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _raw_signature_map(raw_df: pd.DataFrame) -> Dict[int, Tuple[str, str]]:
    if raw_df is None or raw_df.empty or "row_id" not in raw_df.columns:
        return {}
    out: Dict[int, Tuple[str, str]] = {}
    for row in raw_df.to_dict(orient="records"):
        try:
            rid = int(float(row.get("row_id")))
        except Exception:
            continue
        out[rid] = (
            _norm_for_cache_compare(row.get("question", "")),
            _norm_for_cache_compare(row.get("answer", "")),
        )
    return out


def _opinion_cache_is_compatible(
    current_raw_df: pd.DataFrame,
    cached_raw_df: pd.DataFrame,
    cached_opinion_df: pd.DataFrame,
) -> Tuple[bool, str, pd.DataFrame]:
    """Return compatible rows from a previous 02_opinion_units.csv.

    Compatibility is based on row_id + original question/answer, not model/prompt version.
    This lets a new project signature reuse old opinion_units when a new downstream step
    such as Stanza POS is added.
    """
    if cached_opinion_df is None or cached_opinion_df.empty:
        return False, "02_opinion_units.csv kosong", pd.DataFrame(columns=OUTPUT_COLUMNS)

    missing_cols = [c for c in OUTPUT_COLUMNS if c not in cached_opinion_df.columns]
    if missing_cols:
        return False, f"kolom 02_opinion_units tidak kompatibel: {missing_cols[:5]}", pd.DataFrame(columns=OUTPUT_COLUMNS)

    if "row_id" not in cached_opinion_df.columns:
        return False, "kolom row_id tidak ada", pd.DataFrame(columns=OUTPUT_COLUMNS)

    current_map = _raw_signature_map(current_raw_df)
    if not current_map:
        return False, "raw dataset saat ini kosong/tidak valid", pd.DataFrame(columns=OUTPUT_COLUMNS)

    # Prefer checking against cached 01_raw_dataset.csv when available.
    cached_map = _raw_signature_map(cached_raw_df) if cached_raw_df is not None and not cached_raw_df.empty else {}

    compatible_ids = []
    if cached_map:
        for rid, sig in current_map.items():
            if rid in cached_map and cached_map[rid] == sig:
                compatible_ids.append(rid)
    else:
        # Fallback: check question/answer stored in 02_opinion_units.csv.
        for rid, sig in current_map.items():
            subset = cached_opinion_df[pd.to_numeric(cached_opinion_df["row_id"], errors="coerce").fillna(-1).astype(int) == rid]
            if subset.empty:
                continue
            cached_sig = (
                _norm_for_cache_compare(subset.iloc[0].get("question", "")),
                _norm_for_cache_compare(subset.iloc[0].get("answer", "")),
            )
            if cached_sig == sig:
                compatible_ids.append(rid)

    if not compatible_ids:
        return False, "tidak ada row_id question/answer yang cocok", pd.DataFrame(columns=OUTPUT_COLUMNS)

    imported = cached_opinion_df[
        pd.to_numeric(cached_opinion_df["row_id"], errors="coerce").fillna(-1).astype(int).isin(set(compatible_ids))
    ].copy()
    imported = imported.reindex(columns=OUTPUT_COLUMNS)

    if imported.empty:
        return False, "row kompatibel ditemukan tetapi tidak ada opinion_unit yang bisa diambil", pd.DataFrame(columns=OUTPUT_COLUMNS)

    return True, f"{len(imported)} opinion_unit dari {len(set(compatible_ids))} row kompatibel", imported


def import_compatible_opinion_units_from_cache(
    current_raw_df: pd.DataFrame,
    project_dir: Path,
    *,
    enabled: bool,
    force_existing_target: bool = False,
    log_fn=None,
) -> Tuple[bool, str]:
    """Copy compatible 02_opinion_units.csv from another local_results project.

    This is intentionally data-compatible, not signature-compatible. It solves the case
    where adding a new downstream step changes the project signature, while the older
    project already has a valid 02_opinion_units.csv for the same CSV rows.
    """
    if not enabled:
        return False, "fitur import cache lama OFF"

    target = project_dir / "02_opinion_units.csv"
    if target.exists() and not force_existing_target:
        return False, "02_opinion_units.csv sudah ada di project saat ini"

    projects_root = LOCAL_RESULTS_DIR / "projects"
    if not projects_root.exists():
        return False, f"folder projects belum ada: {projects_root}"

    candidates = []
    for candidate_dir in projects_root.iterdir():
        if not candidate_dir.is_dir():
            continue
        try:
            if candidate_dir.resolve() == project_dir.resolve():
                continue
        except Exception:
            pass
        opinion_path = candidate_dir / "02_opinion_units.csv"
        if opinion_path.exists() and opinion_path.stat().st_size > 0:
            try:
                mtime = opinion_path.stat().st_mtime
            except Exception:
                mtime = 0
            candidates.append((mtime, candidate_dir, opinion_path))

    candidates.sort(reverse=True, key=lambda x: x[0])

    checked = 0
    for _, candidate_dir, opinion_path in candidates:
        checked += 1
        try:
            cached_opinion = safe_read_csv(opinion_path, OUTPUT_COLUMNS)
            cached_raw_path = candidate_dir / "01_raw_dataset.csv"
            cached_raw = safe_read_csv(cached_raw_path) if cached_raw_path.exists() else pd.DataFrame()
            ok, reason, imported = _opinion_cache_is_compatible(current_raw_df, cached_raw, cached_opinion)
            if not ok:
                continue

            project_dir.mkdir(parents=True, exist_ok=True)
            save_df(imported, target)
            (project_dir / "02_opinion_units_imported_from.txt").write_text(
                f"Imported at: {datetime.now().isoformat(timespec='seconds')}\n"
                f"Source project: {candidate_dir}\n"
                f"Reason: {reason}\n",
                encoding="utf-8",
            )
            msg = f"Berhasil import cache 02_opinion_units dari {candidate_dir.name}: {reason}"
            if log_fn is not None:
                log_fn(msg)
            return True, msg
        except Exception as e:
            if log_fn is not None:
                log_fn(f"Lewati kandidat cache {candidate_dir.name}: {str(e).replace(chr(10), ' ')[:200]}")
            continue

    return False, f"tidak menemukan 02_opinion_units kompatibel setelah cek {checked} project"


# ============================================================
# RAW-DATASET BASED CACHE IMPORT
# ============================================================

RAW_CACHE_OUTPUT_FILES = [
    "02_opinion_units.csv",
    "02_errors.csv",
    "raw_llm_responses.jsonl",
    "02c_opinion_units_pos.csv",
    "02c_pos_errors.csv",
    "03_candidate_codes.csv",
    "03_candidate_errors.csv",
    "04_candidate_summary.csv",
    "05_candidate_code_normalized.csv",
    "05_candidate_code_mapping.csv",
    "05_candidate_normalization_errors.csv",
    "06_candidate_summary_normalized.csv",
]


def _raw_rows_for_exact_compare(raw_df: pd.DataFrame) -> List[Tuple[int, str, str]]:
    """Build stable row signatures from 01_raw_dataset.csv.

    The comparison intentionally uses the light/raw columns only: row_id + question + answer.
    This avoids relying on opinion_units, prompt version, model, or downstream outputs.
    """
    if raw_df is None or raw_df.empty:
        return []
    required = {"row_id", "question", "answer"}
    if not required.issubset(set(raw_df.columns)):
        return []

    rows: List[Tuple[int, str, str]] = []
    for row in raw_df.to_dict(orient="records"):
        try:
            rid = int(float(row.get("row_id")))
        except Exception:
            continue
        rows.append((
            rid,
            _norm_for_cache_compare(row.get("question", "")),
            _norm_for_cache_compare(row.get("answer", "")),
        ))
    rows.sort(key=lambda x: x[0])
    return rows


def _raw_dataset_exact_match(current_raw_df: pd.DataFrame, cached_raw_df: pd.DataFrame) -> bool:
    current_rows = _raw_rows_for_exact_compare(current_raw_df)
    cached_rows = _raw_rows_for_exact_compare(cached_raw_df)
    return bool(current_rows) and current_rows == cached_rows


def _latest_mtime_for_files(project_path: Path, filenames: List[str]) -> float:
    mtimes = []
    for name in filenames + ["01_raw_dataset.csv"]:
        path = project_path / name
        if path.exists():
            try:
                mtimes.append(path.stat().st_mtime)
            except Exception:
                pass
    return max(mtimes) if mtimes else 0.0


def find_projects_with_same_raw_dataset(
    current_raw_df: pd.DataFrame,
    project_dir: Path,
    *,
    comparison_entities: Optional[List[Dict[str, Any]]] = None,
    log_fn=None,
) -> List[Path]:
    projects_root = LOCAL_RESULTS_DIR / "projects"
    if not projects_root.exists():
        return []

    matches: List[Tuple[float, Path]] = []
    checked = 0
    for candidate_dir in projects_root.iterdir():
        if not candidate_dir.is_dir():
            continue
        try:
            if candidate_dir.resolve() == project_dir.resolve():
                continue
        except Exception:
            pass

        raw_path = candidate_dir / "01_raw_dataset.csv"
        if not raw_path.exists() or raw_path.stat().st_size == 0:
            continue

        checked += 1
        try:
            if comparison_entities is not None:
                candidate_settings = project_load_manifest(candidate_dir).get("settings") or {}
                if candidate_settings.get("comparison_entities") != comparison_entities:
                    continue
            cached_raw = safe_read_csv(raw_path)
            if _raw_dataset_exact_match(current_raw_df, cached_raw):
                matches.append((_latest_mtime_for_files(candidate_dir, RAW_CACHE_OUTPUT_FILES), candidate_dir))
        except Exception as e:
            if log_fn is not None:
                log_fn(f"Lewati project cache {candidate_dir.name}: raw dataset tidak bisa dicek ({str(e)[:120]})")

    matches.sort(reverse=True, key=lambda x: x[0])
    if log_fn is not None:
        log_fn(f"Cek cache raw dataset: {checked} project dicek, {len(matches)} project cocok.")
    return [p for _, p in matches]


def import_latest_outputs_from_same_raw_cache(
    current_raw_df: pd.DataFrame,
    project_dir: Path,
    *,
    enabled: bool,
    force_rerun: bool,
    comparison_entities: Optional[List[Dict[str, Any]]] = None,
    log_fn=None,
) -> Dict[str, Any]:
    """Import newest available outputs from projects with identical 01_raw_dataset.csv.

    If the uploaded CSV normalizes to the same 01_raw_dataset.csv as a previous project,
    downstream outputs can be reused even when the new project signature changed because
    of model/prompt/step-version settings. For repeated runs, the newest modified file is used.
    """
    report: Dict[str, Any] = {"enabled": enabled, "imported": [], "skipped": [], "matched_projects": []}

    if not enabled:
        report["skipped"].append("fitur cache raw dataset OFF")
        return report

    if force_rerun:
        report["skipped"].append("Paksa rerun step ON, cache lama tidak diambil")
        if log_fn is not None:
            log_fn("Import cache raw dataset dilewati karena Paksa rerun step ON.")
        return report

    matches = find_projects_with_same_raw_dataset(
        current_raw_df,
        project_dir,
        comparison_entities=comparison_entities,
        log_fn=log_fn,
    )
    report["matched_projects"] = [str(p) for p in matches]
    if not matches:
        report["skipped"].append("tidak ada project lama dengan 01_raw_dataset.csv yang sama")
        return report

    project_dir.mkdir(parents=True, exist_ok=True)

    for filename in RAW_CACHE_OUTPUT_FILES:
        target = project_dir / filename
        if target.exists() and target.stat().st_size > 0:
            report["skipped"].append(f"{filename} sudah ada di project sekarang")
            continue

        best_source = None
        best_mtime = -1.0
        for candidate_dir in matches:
            src = candidate_dir / filename
            if src.exists() and src.stat().st_size > 0:
                try:
                    mtime = src.stat().st_mtime
                except Exception:
                    mtime = 0.0
                if mtime > best_mtime:
                    best_mtime = mtime
                    best_source = src

        if best_source is None:
            report["skipped"].append(f"{filename} tidak ditemukan di cache yang cocok")
            continue

        shutil.copy2(best_source, target)
        imported_msg = f"{filename} <- {best_source.parent.name}"
        report["imported"].append(imported_msg)
        if log_fn is not None:
            log_fn(f"Import cache raw dataset: {imported_msg}")

    (project_dir / "cache_import_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return report


# ============================================================
# PIPELINE
# ============================================================



def rows_to_process_for_opinion(
    raw_df: pd.DataFrame,
    project_dir: Path,
    *,
    force: bool,
    retry_only_error: bool,
) -> pd.DataFrame:
    if force:
        return raw_df.copy()

    opinion_path = project_dir / "02_opinion_units.csv"
    error_path = project_dir / "02_errors.csv"

    if retry_only_error and error_path.exists():
        err_df = safe_read_csv(error_path, ERROR_COLUMNS)
        if not err_df.empty and "row_id" in err_df.columns:
            ids = set(pd.to_numeric(err_df["row_id"], errors="coerce").dropna().astype(int).tolist())
            if ids:
                return raw_df[raw_df["row_id"].astype(int).isin(ids)].copy()

    if opinion_path.exists() and not force:
        done_df = safe_read_csv(opinion_path, OUTPUT_COLUMNS)
        if not done_df.empty and "row_id" in done_df.columns:
            done_ids = set(pd.to_numeric(done_df["row_id"], errors="coerce").dropna().astype(int).tolist())
            return raw_df[~raw_df["row_id"].astype(int).isin(done_ids)].copy()

    return raw_df.copy()


def step_opinion_units(
    raw_df: pd.DataFrame,
    *,
    project_dir: Path,
    model_id: str,
    force_all_comparative: bool,
    comparison_entities: Optional[List[ComparisonEntity]],
    retry_per_call: int,
    always_retry_per_call: bool,
    timeout_seconds: int,
    retry_only_error: bool,
    force: bool,
    save_raw_responses: bool,
    progress_bar=None,
    status_box=None,
    log_fn=None,
    update_timer_fn=None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    opinion_path = project_dir / "02_opinion_units.csv"
    error_path = project_dir / "02_errors.csv"
    raw_log_path = project_dir / "raw_llm_responses.jsonl" if save_raw_responses else None

    existing_opinion = pd.DataFrame(columns=OUTPUT_COLUMNS)
    if opinion_path.exists() and not force:
        existing_opinion = safe_read_csv(opinion_path, OUTPUT_COLUMNS)
    elif opinion_path.exists() and retry_only_error:
        # Kalau retry row error, pertahankan hasil sukses lama, lalu update row error.
        existing_opinion = safe_read_csv(opinion_path, OUTPUT_COLUMNS)
    existing_errors = pd.DataFrame(columns=ERROR_COLUMNS)
    if error_path.exists() and retry_only_error:
        existing_errors = safe_read_csv(error_path, ERROR_COLUMNS)

    todo_df = rows_to_process_for_opinion(
        raw_df,
        project_dir,
        force=force,
        retry_only_error=retry_only_error,
    )

    if todo_df.empty:
        return existing_opinion, existing_errors

    # Hapus hasil/error lama untuk row yang akan diproses ulang.
    todo_ids = set(todo_df["row_id"].astype(int).tolist())
    if not existing_opinion.empty and "row_id" in existing_opinion.columns:
        existing_opinion = existing_opinion[~existing_opinion["row_id"].astype(int).isin(todo_ids)].copy()
    if not existing_errors.empty and "row_id" in existing_errors.columns:
        existing_errors = existing_errors[~existing_errors["row_id"].astype(int).isin(todo_ids)].copy()

    out_rows: List[Dict[str, Any]] = []
    err_rows: List[Dict[str, Any]] = []
    total = len(todo_df)

    for idx, row in enumerate(todo_df.itertuples(index=False), start=1):
        row_id = int(getattr(row, "row_id"))
        question = str(getattr(row, "question", "") or "")
        answer = str(getattr(row, "answer", "") or "")
        answer_python_cleaned = str(getattr(row, "answer_python_cleaned", "") or "")

        if status_box is not None:
            status_box.write(f"Memproses opinion_units row {idx}/{total} (row_id={row_id})...")
        if log_fn is not None:
            log_fn(f"Mulai row {idx}/{total} (row_id={row_id}).")
        if progress_bar is not None:
            progress_bar.progress(min(0.95, idx / max(total, 1)))

        try:
            if not answer.strip():
                raise ValueError("Answer kosong.")

            matched_entity_names = set(
                match_entities(question, comparison_entities or [])
            )
            row_entities = [
                entity
                for entity in (comparison_entities or [])
                if entity.name in matched_entity_names
            ]
            payload = {
                "row_id": row_id,
                "question": question,
                "answer_original": answer,
                "answer_python_cleaned": answer_python_cleaned,
                "force_comparative": bool(force_all_comparative),
                "comparison_entities": [
                    entity.as_dict() for entity in row_entities
                ],
            }
            obj = call_llm_json(
                f"{OPINION_UNITS_SYSTEM_PROMPT}\n\n{ENTITY_CONTEXT_RULES}",
                payload,
                model_id=model_id,
                timeout_seconds=timeout_seconds,
                retry_per_call=retry_per_call,
                always_retry_per_call=always_retry_per_call,
                raw_log_path=raw_log_path,
                log_fn=log_fn,
                update_timer_fn=update_timer_fn,
                bypass_cache=force,
            )

            answer_cleaned = str(obj.get("answer_cleaned") or answer_python_cleaned or answer).strip()
            items = obj.get("items")
            if not isinstance(items, list) or len(items) == 0:
                raise ValueError("LLM tidak menghasilkan items opinion_unit.")

            row_out_rows: List[Dict[str, Any]] = []
            for j, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                opinion_unit = str(item.get("opinion_unit") or "").strip()
                main_opinion = str(item.get("main_opinion") or "").strip()
                if not opinion_unit or not main_opinion:
                    continue

                main_entity = str(item.get("main_entity") or "").strip()
                counterpart_entity = str(item.get("counterpart_entity") or "").strip()
                if row_entities:
                    main_entity = canonicalize_entity(main_entity, row_entities)
                    counterpart_entity = canonicalize_entity(
                        counterpart_entity,
                        row_entities,
                    )
                    if not main_entity or not counterpart_entity:
                        raise ValueError(
                            "LLM menghasilkan entity di luar daftar hal yang dibandingkan."
                        )
                    if main_entity == counterpart_entity:
                        raise ValueError(
                            "Main entity dan counterpart entity tidak boleh sama."
                        )

                opinion_id = f"r{row_id}_o{j}"
                global_opinion_id = f"{row_id:06d}_{j:03d}"
                row_out_rows.append({
                    "global_opinion_id": global_opinion_id,
                    "row_id": row_id,
                    "question": question,
                    "answer": answer,
                    "answer_python_cleaned": answer_python_cleaned,
                    "answer_cleaned": answer_cleaned,
                    "opinion_id": opinion_id,
                    "opinion_unit": opinion_unit,
                    "main_entity": main_entity,
                    "main_opinion": main_opinion,
                    "main_sentiment": str(item.get("main_sentiment") or "neutral").strip(),
                    "main_source": str(item.get("main_source") or "explicit").strip(),
                    "main_evidence_text": str(item.get("main_evidence_text") or "").strip(),
                    "counterpart_entity": counterpart_entity,
                    "counterpart_opinion": str(item.get("counterpart_opinion") or "").strip(),
                    "counterpart_sentiment": str(item.get("counterpart_sentiment") or "neutral").strip(),
                    "counterpart_source": str(item.get("counterpart_source") or "none").strip(),
                    "counterpart_evidence_text": str(item.get("counterpart_evidence_text") or "").strip(),
                    "counterpart_logic": str(item.get("counterpart_logic") or "not_available").strip(),
                    "confidence": str(item.get("confidence") or "medium").strip(),
                })

            if not row_out_rows:
                raise ValueError("Semua item LLM kosong/tidak valid.")
            out_rows.extend(row_out_rows)
            if log_fn is not None:
                log_fn(
                    f"Row {row_id}: berhasil menghasilkan "
                    f"{len(row_out_rows)} opinion_unit."
                )

        except Exception as e:
            if log_fn is not None:
                log_fn(f"Row {row_id}: masuk 02_errors.csv. Error: {str(e).replace(chr(10), " ")[:350]}")
            err_rows.append({
                "row_id": row_id,
                "question": question,
                "answer": answer,
                "answer_python_cleaned": answer_python_cleaned,
                "step": "opinion_units",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            })

        # Simpan incrementally supaya hasil tidak hilang kalau Streamlit berhenti.
        combined_opinion = pd.concat([existing_opinion, pd.DataFrame(out_rows)], ignore_index=True)
        combined_errors = pd.concat([existing_errors, pd.DataFrame(err_rows)], ignore_index=True)
        combined_opinion = combined_opinion.reindex(columns=OUTPUT_COLUMNS)
        combined_errors = combined_errors.reindex(columns=ERROR_COLUMNS)
        save_df(combined_opinion, opinion_path)
        save_df(combined_errors, error_path)
        if update_timer_fn is not None:
            update_timer_fn()

    final_opinion = safe_read_csv(opinion_path, OUTPUT_COLUMNS)
    final_errors = safe_read_csv(error_path, ERROR_COLUMNS)
    return final_opinion, final_errors



# ============================================================
# STANZA POS TAGGING
# ============================================================





def rows_to_process_for_pos(
    opinion_df: pd.DataFrame,
    project_dir: Path,
    *,
    force: bool,
) -> pd.DataFrame:
    if force:
        return opinion_df.copy()

    pos_path = project_dir / "02c_opinion_units_pos.csv"
    if pos_path.exists() and not force:
        done_df = safe_read_csv(pos_path, POS_COLUMNS)
        if not done_df.empty and "global_opinion_id" in done_df.columns:
            done_ids = set(done_df["global_opinion_id"].astype(str).tolist())
            return opinion_df[~opinion_df["global_opinion_id"].astype(str).isin(done_ids)].copy()
    return opinion_df.copy()


def step_pos_tagging(
    opinion_df: pd.DataFrame,
    *,
    project_dir: Path,
    stanza_lang: str,
    auto_download_stanza: bool,
    force: bool,
    progress_bar=None,
    status_box=None,
    log_fn=None,
    update_timer_fn=None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    pos_path = project_dir / "02c_opinion_units_pos.csv"
    pos_error_path = project_dir / "02c_pos_errors.csv"

    if opinion_df is None or opinion_df.empty:
        raise RuntimeError("02_opinion_units.csv kosong. Jalankan opinion_units dulu sebelum POS tagging.")

    existing_pos = pd.DataFrame(columns=POS_COLUMNS)
    if pos_path.exists() and not force:
        existing_pos = safe_read_csv(pos_path, POS_COLUMNS)
    existing_errors = safe_read_csv(pos_error_path) if pos_error_path.exists() else pd.DataFrame(columns=[
        "global_opinion_id", "row_id", "step", "error_type", "error_message", "traceback"
    ])

    todo_df = rows_to_process_for_pos(opinion_df, project_dir, force=force)
    if todo_df.empty:
        return existing_pos, existing_errors

    if log_fn is not None:
        log_fn(f"Memuat Stanza pipeline bahasa '{stanza_lang}'...")
    nlp = load_stanza_pipeline(stanza_lang, auto_download_stanza)
    if log_fn is not None:
        log_fn("Stanza pipeline siap.")

    todo_ids = set(todo_df["global_opinion_id"].astype(str).tolist())
    if not existing_pos.empty and "global_opinion_id" in existing_pos.columns:
        existing_pos = existing_pos[~existing_pos["global_opinion_id"].astype(str).isin(todo_ids)].copy()
    if not existing_errors.empty and "global_opinion_id" in existing_errors.columns:
        existing_errors = existing_errors[~existing_errors["global_opinion_id"].astype(str).isin(todo_ids)].copy()

    out_rows: List[Dict[str, Any]] = []
    err_rows: List[Dict[str, Any]] = []
    total = len(todo_df)

    for idx, row in enumerate(todo_df.to_dict(orient="records"), start=1):
        gid = str(row.get("global_opinion_id", ""))
        row_id = row.get("row_id", "")
        if status_box is not None:
            status_box.write(f"POS tagging row {idx}/{total} (global_opinion_id={gid})...")
        if log_fn is not None:
            log_fn(f"POS {idx}/{total}: proses global_opinion_id={gid}.")
        if progress_bar is not None:
            progress_bar.progress(min(0.95, idx / max(total, 1)))

        try:
            main_pos, main_nouns = format_pos_and_nouns(row.get("main_opinion", ""), nlp)
            counter_pos, counter_nouns = format_pos_and_nouns(row.get("counterpart_opinion", ""), nlp)
            new_row = dict(row)
            new_row.update({
                "main_pos_tokens": main_pos,
                "counterpart_pos_tokens": counter_pos,
                "main_noun_candidates": main_nouns,
                "counterpart_noun_candidates": counter_nouns,
            })
            out_rows.append(new_row)
        except Exception as e:
            if log_fn is not None:
                log_fn(f"POS {gid}: error. {str(e).replace(chr(10), ' ')[:250]}")
            err_rows.append({
                "global_opinion_id": gid,
                "row_id": row_id,
                "step": "pos_tagging",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            })

        combined_pos = pd.concat([existing_pos, pd.DataFrame(out_rows)], ignore_index=True).reindex(columns=POS_COLUMNS)
        combined_errors = pd.concat([existing_errors, pd.DataFrame(err_rows)], ignore_index=True)
        save_df(combined_pos, pos_path)
        save_df(combined_errors, pos_error_path)
        if update_timer_fn is not None:
            update_timer_fn()

    return safe_read_csv(pos_path, POS_COLUMNS), safe_read_csv(pos_error_path)

# ============================================================
# CANDIDATE CODE + SUMMARY
# ============================================================

def _normalize_candidate_code_text(value: Any) -> str:
    text = "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
    text = unicodedata.normalize("NFKC", text).strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def rows_to_process_for_candidate(
    pos_df: pd.DataFrame,
    project_dir: Path,
    *,
    force: bool,
) -> pd.DataFrame:
    if force:
        return pos_df.copy()

    candidate_path = project_dir / "03_candidate_codes.csv"
    if candidate_path.exists() and not force:
        done_df = safe_read_csv(candidate_path, CANDIDATE_COLUMNS)
        if not done_df.empty and "global_opinion_id" in done_df.columns:
            done_ids = set(done_df["global_opinion_id"].astype(str).tolist())
            return pos_df[~pos_df["global_opinion_id"].astype(str).isin(done_ids)].copy()
    return pos_df.copy()


def step_candidate_codes(
    pos_df: pd.DataFrame,
    *,
    project_dir: Path,
    model_id: str,
    retry_per_call: int,
    always_retry_per_call: bool,
    timeout_seconds: int,
    force: bool,
    save_raw_responses: bool,
    progress_bar=None,
    status_box=None,
    log_fn=None,
    update_timer_fn=None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    candidate_path = project_dir / "03_candidate_codes.csv"
    error_path = project_dir / "03_candidate_errors.csv"
    raw_log_path = project_dir / "raw_llm_responses.jsonl" if save_raw_responses else None

    existing_candidate = pd.DataFrame(columns=CANDIDATE_COLUMNS)
    if candidate_path.exists() and not force:
        existing_candidate = safe_read_csv(candidate_path, CANDIDATE_COLUMNS)
    existing_errors = pd.DataFrame(columns=CANDIDATE_ERROR_COLUMNS)
    if error_path.exists() and not force:
        existing_errors = safe_read_csv(error_path, CANDIDATE_ERROR_COLUMNS)

    todo_df = rows_to_process_for_candidate(pos_df, project_dir, force=force)
    if todo_df.empty:
        return existing_candidate, existing_errors

    todo_ids = set(todo_df["global_opinion_id"].astype(str).tolist())
    if not existing_candidate.empty and "global_opinion_id" in existing_candidate.columns:
        existing_candidate = existing_candidate[~existing_candidate["global_opinion_id"].astype(str).isin(todo_ids)].copy()
    if not existing_errors.empty and "global_opinion_id" in existing_errors.columns:
        existing_errors = existing_errors[~existing_errors["global_opinion_id"].astype(str).isin(todo_ids)].copy()

    out_rows: List[Dict[str, Any]] = []
    err_rows: List[Dict[str, Any]] = []
    total = len(todo_df)

    for idx, row in enumerate(todo_df.to_dict(orient="records"), start=1):
        gid = str(row.get("global_opinion_id", ""))
        row_id = row.get("row_id", "")
        if status_box is not None:
            status_box.write(f"Membuat candidate_code {idx}/{total} (global_opinion_id={gid})...")
        if log_fn is not None:
            log_fn(f"Candidate {idx}/{total}: proses global_opinion_id={gid}.")
        if progress_bar is not None:
            progress_bar.progress(min(0.95, idx / max(total, 1)))

        try:
            payload = {
                "row_id": row_id,
                "global_opinion_id": gid,
                "question": row.get("question", ""),
                "answer": row.get("answer", ""),
                "opinion_unit": row.get("opinion_unit", ""),
                "main_entity": row.get("main_entity", ""),
                "main_opinion": row.get("main_opinion", ""),
                "main_sentiment": row.get("main_sentiment", ""),
                "counterpart_entity": row.get("counterpart_entity", ""),
                "counterpart_opinion": row.get("counterpart_opinion", ""),
                "counterpart_sentiment": row.get("counterpart_sentiment", ""),
                "main_pos_tokens": row.get("main_pos_tokens", ""),
                "counterpart_pos_tokens": row.get("counterpart_pos_tokens", ""),
                "main_noun_candidates": row.get("main_noun_candidates", ""),
                "counterpart_noun_candidates": row.get("counterpart_noun_candidates", ""),
            }
            obj = call_llm_json(
                CANDIDATE_CODE_SYSTEM_PROMPT,
                payload,
                model_id=model_id,
                timeout_seconds=timeout_seconds,
                retry_per_call=retry_per_call,
                always_retry_per_call=always_retry_per_call,
                raw_log_path=raw_log_path,
                log_fn=log_fn,
                update_timer_fn=update_timer_fn,
                bypass_cache=force,
            )

            candidate_code = _normalize_candidate_code_text(obj.get("candidate_code", ""))
            if not candidate_code:
                raise ValueError("LLM tidak menghasilkan candidate_code.")

            out_rows.append({
                "global_opinion_id": gid,
                "row_id": row_id,
                "question": row.get("question", ""),
                "answer": row.get("answer", ""),
                "opinion_id": row.get("opinion_id", ""),
                "opinion_unit": row.get("opinion_unit", ""),
                "main_entity": row.get("main_entity", ""),
                "main_opinion": row.get("main_opinion", ""),
                "main_sentiment": row.get("main_sentiment", ""),
                "counterpart_entity": row.get("counterpart_entity", ""),
                "counterpart_opinion": row.get("counterpart_opinion", ""),
                "counterpart_sentiment": row.get("counterpart_sentiment", ""),
                "main_pos_tokens": row.get("main_pos_tokens", ""),
                "counterpart_pos_tokens": row.get("counterpart_pos_tokens", ""),
                "main_noun_candidates": row.get("main_noun_candidates", ""),
                "counterpart_noun_candidates": row.get("counterpart_noun_candidates", ""),
                "candidate_code": candidate_code,
                "main_position": str(obj.get("main_position") or "").strip(),
                "counterpart_position": str(obj.get("counterpart_position") or "").strip(),
                "candidate_reason": str(obj.get("candidate_reason") or "").strip(),
                "candidate_confidence": str(obj.get("confidence") or "medium").strip(),
            })
            if log_fn is not None:
                log_fn(f"Candidate {gid}: berhasil â†’ {candidate_code}")

        except Exception as e:
            if log_fn is not None:
                log_fn(f"Candidate {gid}: masuk 03_candidate_errors.csv. Error: {str(e).replace(chr(10), ' ')[:250]}")
            err_rows.append({
                "global_opinion_id": gid,
                "row_id": row_id,
                "opinion_unit": row.get("opinion_unit", ""),
                "step": "candidate_codes",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc(),
            })

        combined_candidate = pd.concat([existing_candidate, pd.DataFrame(out_rows)], ignore_index=True).reindex(columns=CANDIDATE_COLUMNS)
        combined_errors = pd.concat([existing_errors, pd.DataFrame(err_rows)], ignore_index=True).reindex(columns=CANDIDATE_ERROR_COLUMNS)
        save_df(combined_candidate, candidate_path)
        save_df(combined_errors, error_path)
        if update_timer_fn is not None:
            update_timer_fn()

    return safe_read_csv(candidate_path, CANDIDATE_COLUMNS), safe_read_csv(error_path, CANDIDATE_ERROR_COLUMNS)


def build_candidate_summary(candidate_df: pd.DataFrame, *, project_dir: Path, force: bool) -> pd.DataFrame:
    summary_path = project_dir / "04_candidate_summary.csv"
    if summary_path.exists() and not force:
        return safe_read_csv(summary_path, SUMMARY_COLUMNS)

    if candidate_df is None or candidate_df.empty:
        summary_df = pd.DataFrame(columns=SUMMARY_COLUMNS)
        save_df(summary_df, summary_path)
        return summary_df

    df = candidate_df.copy()
    df["candidate_code"] = df["candidate_code"].map(_normalize_candidate_code_text)
    df = df[df["candidate_code"].astype(str).str.len() > 0].copy()

    rows: List[Dict[str, Any]] = []
    for code, g in df.groupby("candidate_code", dropna=False):
        def uniq_join(col: str, limit: int = 30) -> str:
            vals = []
            if col in g.columns:
                for v in g[col].fillna("").astype(str).tolist():
                    v = v.strip()
                    if v and v not in vals:
                        vals.append(v)
            return " | ".join(vals[:limit])

        samples = []
        for v in g.get("opinion_unit", pd.Series(dtype=str)).fillna("").astype(str).tolist():
            v = v.strip()
            if v and v not in samples:
                samples.append(v)
            if len(samples) >= 5:
                break

        rows.append({
            "candidate_code": code,
            "frequency": int(len(g)),
            "supporting_opinion_ids": uniq_join("global_opinion_id", limit=200),
            "sample_opinion_units": " || ".join(samples),
            "main_entities": uniq_join("main_entity"),
            "counterpart_entities": uniq_join("counterpart_entity"),
            "sentiments": uniq_join("main_sentiment"),
            "main_positions": uniq_join("main_position"),
            "counterpart_positions": uniq_join("counterpart_position"),
            "candidate_reasons": uniq_join("candidate_reason", limit=10),
        })

    summary_df = pd.DataFrame(rows).reindex(columns=SUMMARY_COLUMNS)
    if not summary_df.empty:
        summary_df = summary_df.sort_values(["frequency", "candidate_code"], ascending=[False, True]).reset_index(drop=True)
    save_df(summary_df, summary_path)
    return summary_df


# ============================================================
# CANDIDATE NORMALIZATION
# ============================================================

def _split_text_list(value: Any) -> List[str]:
    text = "" if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
    parts = re.split(r"\s*(?:\|\||\||;|,)\s*", text)
    out = []
    for p in parts:
        p = p.strip()
        if p and p not in out:
            out.append(p)
    return out


def _safe_int_value(value: Any, default: int = 0) -> int:
    try:
        num = pd.to_numeric(value, errors="coerce")
        if pd.isna(num):
            return default
        return int(num)
    except Exception:
        return default




def _python_candidate_prefilter(code: str) -> str:
    return candidate_prefilter(code, _normalize_candidate_code_text)


def _normalization_payload_from_summary(summary_df: pd.DataFrame) -> Dict[str, Any]:
    """Payload global: seluruh candidate_code unik dikirim dalam satu request LLM.

    Normalisasi butuh pandangan global. Kalau dibuat batch, candidate_code mirip
    yang berada di batch berbeda bisa gagal digabung.
    """
    items = []
    for row in summary_df.to_dict(orient="records"):
        items.append({
            "original_candidate_code": str(row.get("candidate_code", "")).strip(),
            "frequency": _safe_int_value(row.get("frequency", 0)),
            "sample_opinion_units": str(row.get("sample_opinion_units", ""))[:1500],
            "sample_main_positions": str(row.get("main_positions", ""))[:700],
            "sample_counterpart_positions": str(row.get("counterpart_positions", ""))[:700],
            "candidate_reasons": str(row.get("candidate_reasons", ""))[:700],
        })
    return {
        "normalization_mode": "global_single_call",
        "instruction": "Baca seluruh items sebagai satu daftar global. Hindari dua kesalahan dengan bobot sama: over-merge dan under-merge. (1) Turunkan daftar kepala generik khusus dataset ini, (2) WAJIB gabungkan semua sinonim/varian ejaan/varian morfologis/sinonim kepala, (3) jangan gabungkan pembatas yang berbeda dan jangan pakai kepala telanjang, (4) pilih label paling spesifik per kelompok, (5) audit recoverability dan audit under-merge. Hasil tanpa merge sama sekali hampir pasti salah. PENTING UNTUK OUTPUT: di 'items' keluarkan HANYA original_candidate_code yang BERUBAH (normalization_action 'merge', 'rename', atau 'specificize'); code yang dipertahankan apa adanya (keep) JANGAN dimasukkan. Wajib sertakan field top-level 'reviewed_count' = jumlah seluruh original_candidate_code yang kamu tinjau (harus sama dengan total_unique_candidate_codes). normalization_reason maksimal 12 kata.",
        "total_unique_candidate_codes": len(items),
        "items": items,
    }


# ============================================================
# DOMAIN-AGNOSTIC OVER-MERGE GUARD (LLM-driven relabel)
# Tidak ada wordlist domain. Sinyal over-merge dideteksi secara
# struktural (kepala telanjang memayungi pembatas berbeda) dan ambang
# genericity diturunkan dari data itu sendiri. Perbaikan utama lewat
# LLM relabel; fallback deterministik (split) hanya jaring pengaman.
# ============================================================









def relabel_overmerged_groups(
    flagged: Dict[str, List[str]],
    summary_df,
    *,
    model_id: str,
    timeout_seconds: int,
    retry_per_call: int,
    always_retry_per_call: bool,
    raw_log_path=None,
    log_fn=None,
    update_timer_fn=None,
    bypass_cache: bool = False,
) -> Dict[str, Dict[str, str]]:
    sample_map = dict(zip(summary_df["candidate_code"], summary_df.get("sample_opinion_units", pd.Series([""] * len(summary_df)))))
    groups_payload = []
    for label, members in flagged.items():
        groups_payload.append({
            "label_terlalu_umum": label,
            "members": [
                {"candidate_code": m, "sample_opinion_units": str(sample_map.get(m, ""))[:600]}
                for m in members
            ],
        })
    payload = {
        "task": "relabel_overmerged_groups",
        "instruction": "Setiap grup memakai label kepala-telanjang terlalu umum padahal anggotanya punya pembatas berbeda. Pecah atau sub-merge ke label spesifik. Jangan pakai kepala telanjang.",
        "groups": groups_payload,
    }
    obj = call_llm_json(
        RELABEL_SYSTEM_PROMPT,
        payload,
        model_id=model_id,
        timeout_seconds=timeout_seconds,
        retry_per_call=retry_per_call,
        always_retry_per_call=always_retry_per_call,
        raw_log_path=raw_log_path,
        log_fn=log_fn,
        update_timer_fn=update_timer_fn,
        bypass_cache=bypass_cache,
    )
    items = obj.get("items", []) if isinstance(obj, dict) else []
    out: Dict[str, Dict[str, str]] = {}
    if isinstance(items, list):
        for it in items:
            orig = _normalize_candidate_code_text(it.get("original_candidate_code", ""))
            norm = _normalize_candidate_code_text(it.get("normalized_candidate_code", ""))
            if orig and norm:
                out[orig] = {
                    "normalized_candidate_code": norm,
                    "normalization_action": str(it.get("normalization_action") or "specificize").strip(),
                    "normalization_reason": str(it.get("normalization_reason") or "Relabel dari label terlalu umum.").strip(),
                    "normalization_confidence": str(it.get("confidence") or "medium").strip(),
                }
    return out


def enforce_aspect_granularity(
    mappings: Dict[str, Dict[str, str]],
    summary_df,
    *,
    model_id: str,
    timeout_seconds: int,
    retry_per_call: int,
    always_retry_per_call: bool,
    raw_log_path=None,
    log_fn=None,
    update_timer_fn=None,
    bypass_cache: bool = False,
    max_iter: int = 2,
):
    """Loop: deteksi over-merge struktural -> minta LLM relabel/pecah -> ulang.
    Sisa over-merge yang masih ada setelah max_iter dipecah deterministik (split).
    Mengembalikan (mappings, generic_heads, relabel_info)."""
    generic_heads = derive_generic_heads_from_data(list(mappings.keys()))
    relabel_info: Dict[str, str] = {}
    for _ in range(max(1, int(max_iter))):
        flagged = detect_overmerged_labels(mappings)
        if not flagged:
            break
        if log_fn is not None:
            log_fn(f"Guard over-merge: {len(flagged)} label payung terdeteksi -> {list(flagged.keys())}")
        applied: Dict[str, Dict[str, str]] = {}
        try:
            applied = relabel_overmerged_groups(
                flagged, summary_df,
                model_id=model_id, timeout_seconds=timeout_seconds,
                retry_per_call=retry_per_call, always_retry_per_call=always_retry_per_call,
                raw_log_path=raw_log_path, log_fn=log_fn, update_timer_fn=update_timer_fn,
                bypass_cache=bypass_cache,
            )
        except Exception as e:
            if log_fn is not None:
                log_fn(f"Guard relabel LLM gagal: {str(e)[:160]}; lanjut ke fallback deterministik.")
            applied = {}
        flagged_members = {m for members in flagged.values() for m in members}
        for m in flagged_members:
            new = applied.get(m)
            if new and new.get("normalized_candidate_code"):
                mappings[m].update(new)
                relabel_info[m] = new["normalized_candidate_code"]
    # Sweep terakhir: apa pun yang MASIH over-merge dipecah secara deterministik.
    flagged = detect_overmerged_labels(mappings)
    for label, members in flagged.items():
        for m in members:
            specific = _python_candidate_prefilter(m) or m
            mappings[m]["normalized_candidate_code"] = specific
            mappings[m]["normalization_action"] = "specificize"
            mappings[m]["normalization_reason"] = "Dipisah dari label terlalu umum (fallback deterministik domain-agnostik)."
            mappings[m]["normalization_confidence"] = mappings[m].get("normalization_confidence", "low")
            relabel_info[m] = specific
    return mappings, generic_heads, relabel_info


def step_candidate_normalization(
    candidate_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    *,
    project_dir: Path,
    model_id: str,
    retry_per_call: int,
    always_retry_per_call: bool,
    timeout_seconds: int,
    force: bool,
    save_raw_responses: bool,
    batch_size: int = 25,
    progress_bar=None,
    status_box=None,
    log_fn=None,
    update_timer_fn=None,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    normalized_path = project_dir / "05_candidate_code_normalized.csv"
    mapping_path = project_dir / "05_candidate_code_mapping.csv"
    error_path = project_dir / "05_candidate_normalization_errors.csv"
    raw_log_path = project_dir / "raw_llm_responses.jsonl" if save_raw_responses else None

    if normalized_path.exists() and mapping_path.exists() and not force:
        return safe_read_csv(normalized_path, NORMALIZED_COLUMNS), safe_read_csv(mapping_path, NORMALIZATION_MAPPING_COLUMNS)
    if candidate_df is None or candidate_df.empty:
        empty_norm = pd.DataFrame(columns=NORMALIZED_COLUMNS)
        empty_map = pd.DataFrame(columns=NORMALIZATION_MAPPING_COLUMNS)
        save_df(empty_norm, normalized_path)
        save_df(empty_map, mapping_path)
        save_df(pd.DataFrame(columns=["batch", "error_type", "error_message", "traceback"]), error_path)
        return empty_norm, empty_map

    if summary_df is None or summary_df.empty:
        summary_df = build_candidate_summary(candidate_df, project_dir=project_dir, force=True)

    summary_df = summary_df.copy()
    summary_df["candidate_code"] = summary_df["candidate_code"].map(_normalize_candidate_code_text)
    summary_df = summary_df[summary_df["candidate_code"].str.len() > 0].drop_duplicates("candidate_code").reset_index(drop=True)

    mappings: Dict[str, Dict[str, str]] = {}
    err_rows: List[Dict[str, Any]] = []
    total = len(summary_df)

    if status_box is not None:
        status_box.write(f"Normalisasi global {total} candidate_code unik dalam 1 request LLM...")
    if log_fn is not None:
        log_fn(f"Normalisasi global candidate_code: {total} candidate_code unik dikirim dalam 1 request LLM.")
    if progress_bar is not None:
        progress_bar.progress(0.72)

    try:
        obj = call_llm_json(
            CANDIDATE_NORMALIZATION_SYSTEM_PROMPT,
            _normalization_payload_from_summary(summary_df),
            model_id=model_id,
            timeout_seconds=timeout_seconds,
            retry_per_call=retry_per_call,
            always_retry_per_call=always_retry_per_call,
            raw_log_path=raw_log_path,
            log_fn=log_fn,
            update_timer_fn=update_timer_fn,
            bypass_cache=force,
        )
        items = obj.get("items", [])
        if not isinstance(items, list):
            raise ValueError("Output normalisasi tidak memiliki items list.")
        for item in items:
            orig = _normalize_candidate_code_text(item.get("original_candidate_code", ""))
            norm = _normalize_candidate_code_text(item.get("normalized_candidate_code", ""))
            if not orig:
                continue
            if not norm:
                norm = _python_candidate_prefilter(orig) or orig
            mappings[orig] = {
                "normalized_candidate_code": norm,
                "normalization_action": str(item.get("normalization_action") or "rename").strip(),
                "normalization_reason": str(item.get("normalization_reason") or "").strip(),
                "normalization_confidence": str(item.get("confidence") or "medium").strip(),
            }
        reviewed_count = _safe_int_value(obj.get("reviewed_count", 0))
        changed_count = len(mappings)
        # Kontrak baru: LLM hanya mengeluarkan code yang BERUBAH (merge/rename/specificize).
        # Anggap output gagal/terpotong jika tidak ada perubahan DAN model tidak
        # mengonfirmasi sudah meninjau hampir seluruh daftar.
        if changed_count == 0 and reviewed_count < max(1, int(total * 0.8)):
            raise ValueError(
                f"Output normalisasi diragukan (kemungkinan terpotong): items={changed_count}, "
                f"reviewed_count={reviewed_count} dari total {total}."
            )
        # Semua code yang TIDAK dikembalikan LLM = dipertahankan apa adanya (keep eksplisit, bukan kegagalan).
        for _row in summary_df.to_dict(orient="records"):
            _orig_keep = _normalize_candidate_code_text(_row.get("candidate_code", ""))
            if _orig_keep and _orig_keep not in mappings:
                mappings[_orig_keep] = {
                    "normalized_candidate_code": _orig_keep,
                    "normalization_action": "keep",
                    "normalization_reason": "Tidak diubah LLM (dipertahankan apa adanya).",
                    "normalization_confidence": "high",
                }
        if log_fn is not None:
            log_fn(f"Normalisasi global selesai: {changed_count} perubahan dari {total} code (reviewed_count={reviewed_count}).")
    except Exception as e:
        if log_fn is not None:
            log_fn(f"Normalisasi global gagal, pakai fallback Python konservatif. Error: {str(e).replace(chr(10), ' ')[:250]}")
        err_rows.append({
            "batch": "global",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc(),
        })
        for row in summary_df.to_dict(orient="records"):
            orig = _normalize_candidate_code_text(row.get("candidate_code", ""))
            if not orig:
                continue
            norm = _python_candidate_prefilter(orig) or orig
            mappings[orig] = {
                "normalized_candidate_code": norm,
                "normalization_action": "fallback_keep_or_light_rename",
                "normalization_reason": "LLM normalisasi global gagal; memakai fallback Python konservatif.",
                "normalization_confidence": "low",
            }
    if update_timer_fn is not None:
        update_timer_fn()
    if progress_bar is not None:
        progress_bar.progress(0.95)

    # Pastikan semua candidate_code punya mapping.
    for code in summary_df["candidate_code"].fillna("").astype(str).tolist():
        code = _normalize_candidate_code_text(code)
        if code and code not in mappings:
            norm = _python_candidate_prefilter(code) or code
            mappings[code] = {
                "normalized_candidate_code": norm,
                "normalization_action": "fallback_keep_or_light_rename",
                "normalization_reason": "Tidak dikembalikan LLM; memakai fallback Python konservatif.",
                "normalization_confidence": "low",
            }

    # === Domain-agnostic over-merge guard + LLM relabel ===
    generic_heads_detected, relabel_info = [], {}
    try:
        mappings, generic_heads_detected, relabel_info = enforce_aspect_granularity(
            mappings,
            summary_df,
            model_id=model_id,
            timeout_seconds=timeout_seconds,
            retry_per_call=retry_per_call,
            always_retry_per_call=always_retry_per_call,
            raw_log_path=raw_log_path,
            log_fn=log_fn,
            update_timer_fn=update_timer_fn,
            bypass_cache=force,
        )
    except Exception as _guard_err:
        if log_fn is not None:
            log_fn(f"Guard over-merge dilewati karena error: {str(_guard_err)[:200]}")

    map_rows = []
    freq_map = dict(zip(summary_df["candidate_code"], summary_df.get("frequency", pd.Series([0]*len(summary_df)))))
    sample_map = dict(zip(summary_df["candidate_code"], summary_df.get("sample_opinion_units", pd.Series([""]*len(summary_df)))))
    for orig, meta in sorted(mappings.items()):
        map_rows.append({
            "original_candidate_code": orig,
            "normalized_candidate_code": meta["normalized_candidate_code"],
            "normalization_action": meta["normalization_action"],
            "normalization_reason": meta["normalization_reason"],
            "normalization_confidence": meta["normalization_confidence"],
            "frequency": _safe_int_value(freq_map.get(orig, 0)),
            "sample_opinion_units": str(sample_map.get(orig, "")),
        })
    mapping_df = pd.DataFrame(map_rows).reindex(columns=NORMALIZATION_MAPPING_COLUMNS)

    # Laporan kualitas sederhana agar user bisa melihat apakah normalisasi masih terlalu konservatif.
    try:
        raw_unique_count = int(summary_df["candidate_code"].nunique())
        normalized_unique_count = int(mapping_df["normalized_candidate_code"].nunique()) if not mapping_df.empty else 0
        keep_count = int((mapping_df["normalization_action"].astype(str).str.lower() == "keep").sum()) if not mapping_df.empty else 0
        quality_report = {
            "raw_unique_candidate_codes": raw_unique_count,
            "normalized_unique_candidate_codes": normalized_unique_count,
            "reduction_count": raw_unique_count - normalized_unique_count,
            "reduction_ratio": round((raw_unique_count - normalized_unique_count) / raw_unique_count, 4) if raw_unique_count else 0,
            "keep_count": keep_count,
            "keep_ratio": round(keep_count / raw_unique_count, 4) if raw_unique_count else 0,
            "note": "Jika normalized_unique_candidate_codes masih mendekati raw_unique_candidate_codes, normalisasi masih terlalu konservatif dan prompt/hasil perlu dicek.",
            "generic_heads_detected": generic_heads_detected,
            "overmerge_groups_relabeled": relabel_info,
        }
        (project_dir / "05_candidate_normalization_quality_report.json").write_text(
            json.dumps(quality_report, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if log_fn is not None:
            log_fn(
                f"Normalisasi quality: {raw_unique_count} raw â†’ {normalized_unique_count} normalized "
                f"(turun {quality_report['reduction_count']}, keep {keep_count})."
            )
    except Exception:
        pass

    df = candidate_df.copy()
    df["candidate_code"] = df["candidate_code"].map(_normalize_candidate_code_text)
    df["original_candidate_code"] = df["candidate_code"]
    df["normalized_candidate_code"] = df["candidate_code"].map(lambda c: mappings.get(c, {}).get("normalized_candidate_code", _python_candidate_prefilter(c) or c))
    df["normalization_action"] = df["candidate_code"].map(lambda c: mappings.get(c, {}).get("normalization_action", "fallback_keep_or_light_rename"))
    df["normalization_reason"] = df["candidate_code"].map(lambda c: mappings.get(c, {}).get("normalization_reason", "Fallback konservatif."))
    df["normalization_confidence"] = df["candidate_code"].map(lambda c: mappings.get(c, {}).get("normalization_confidence", "low"))
    normalized_df = df.reindex(columns=NORMALIZED_COLUMNS)

    save_df(normalized_df, normalized_path)
    save_df(mapping_df, mapping_path)
    save_df(pd.DataFrame(err_rows).reindex(columns=["batch", "error_type", "error_message", "traceback"]), error_path)
    return normalized_df, mapping_df


def build_normalized_candidate_summary(normalized_df: pd.DataFrame, *, project_dir: Path, force: bool) -> pd.DataFrame:
    summary_path = project_dir / "06_candidate_summary_normalized.csv"
    if summary_path.exists() and not force:
        return safe_read_csv(summary_path, NORMALIZED_SUMMARY_COLUMNS)

    if normalized_df is None or normalized_df.empty:
        out = pd.DataFrame(columns=NORMALIZED_SUMMARY_COLUMNS)
        save_df(out, summary_path)
        return out

    df = normalized_df.copy()
    df["normalized_candidate_code"] = df["normalized_candidate_code"].map(_normalize_candidate_code_text)
    df = df[df["normalized_candidate_code"].astype(str).str.len() > 0].copy()

    rows: List[Dict[str, Any]] = []
    for code, g in df.groupby("normalized_candidate_code", dropna=False):
        def uniq_join(col: str, limit: int = 30) -> str:
            vals = []
            if col in g.columns:
                for v in g[col].fillna("").astype(str).tolist():
                    v = v.strip()
                    if v and v not in vals:
                        vals.append(v)
            return " | ".join(vals[:limit])

        samples = []
        for v in g.get("opinion_unit", pd.Series(dtype=str)).fillna("").astype(str).tolist():
            v = v.strip()
            if v and v not in samples:
                samples.append(v)
            if len(samples) >= 5:
                break

        rows.append({
            "normalized_candidate_code": code,
            "frequency": int(len(g)),
            "original_candidate_codes": uniq_join("original_candidate_code", limit=80),
            "supporting_opinion_ids": uniq_join("global_opinion_id", limit=300),
            "sample_opinion_units": " || ".join(samples),
            "main_entities": uniq_join("main_entity"),
            "counterpart_entities": uniq_join("counterpart_entity"),
            "sentiments": uniq_join("main_sentiment"),
            "main_positions": uniq_join("main_position"),
            "counterpart_positions": uniq_join("counterpart_position"),
            "candidate_reasons": uniq_join("candidate_reason", limit=10),
            "normalization_reasons": uniq_join("normalization_reason", limit=10),
        })
    out = pd.DataFrame(rows).reindex(columns=NORMALIZED_SUMMARY_COLUMNS)
    if not out.empty:
        out = out.sort_values(["frequency", "normalized_candidate_code"], ascending=[False, True]).reset_index(drop=True)
    save_df(out, summary_path)
    return out

# ============================================================
# UI HELPERS
# ============================================================















def _model_select_index() -> int:
    values = list(OPENROUTER_FREE_MODEL_OPTIONS.values())
    labels = list(OPENROUTER_FREE_MODEL_OPTIONS.keys())
    if LLM_MODEL in values:
        return values.index(LLM_MODEL)
    return labels.index("Custom model dari secrets/env")


def render_advanced_settings() -> Dict[str, Any]:
    ui.render_section_title(
        4,
        "Pilih Mode Analisis",
        "Gunakan preset untuk kebutuhan umum, atau buka mode manual untuk eksperimen teknis.",
    )

    preset = st.radio(
        "Pilih cara menjalankan",
        [
            "Analisis penuh",
            "Cek cepat 10 baris",
            "Ulang dari candidate_code",
            "Ulang normalisasi saja",
            "Manual",
        ],
        horizontal=True,
        help="Preset menyederhanakan opsi teknis. Mode manual membuka kontrol pipeline lengkap.",
    )

    preset_defaults = {
        "Analisis penuh": ("Sampai candidate_summary normalisasi (06)", 0, False, False, ""),
        "Cek cepat 10 baris": ("Sampai candidate_summary normalisasi (06)", 10, False, False, ""),
        "Ulang dari candidate_code": ("Sampai candidate_summary normalisasi (06)", 0, False, True, "Candidate codes (03)"),
        "Ulang normalisasi saja": ("Sampai candidate_summary normalisasi (06)", 0, False, True, "Normalisasi candidate_code (05)"),
        "Manual": ("Sampai candidate_summary normalisasi (06)", 0, False, False, ""),
    }
    default_run_until, default_max_rows, default_force_start, default_force_step_enabled, default_force_step_label = preset_defaults[preset]

    preset_descriptions = {
        "Analisis penuh": ("Analisis penuh", "Memproses semua baris sampai ringkasan aspek ternormalisasi. Cache tetap dipakai jika dataset yang sama sudah pernah diproses."),
        "Cek cepat 10 baris": ("Cek cepat", "Memakai 10 baris pertama untuk memeriksa format CSV, koneksi model, dan bentuk hasil sebelum menjalankan semua data."),
        "Ulang dari candidate_code": ("Ulang aspek", "Memakai opinion unit dan POS lama, lalu membuat ulang candidate_code, normalisasi, dan ringkasan akhir."),
        "Ulang normalisasi saja": ("Ulang normalisasi", "Memakai candidate_code lama, lalu menyatukan ulang aspek serupa dan membangun ringkasan akhir."),
        "Manual": ("Manual", "Membuka kontrol lengkap untuk memilih batas tahap, cache, retry, timeout, dan opsi debug."),
    }
    mode_title, mode_body = preset_descriptions[preset]
    st.markdown(
        f"""
        <div class="mode-help">
            <strong>{mode_title}</strong>
            <p>{mode_body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    force_all_comparative = st.checkbox(
        "Lewati pemeriksaan bentuk pertanyaan",
        value=False,
        help=(
            "Aktifkan hanya jika semua pertanyaan sudah dipastikan komparatif. "
            "Pemeriksaan kemunculan minimal dua hal tetap dijalankan."
        ),
    )

    with st.expander("Pengaturan lanjutan", expanded=(preset == "Manual")):
        model_label = st.selectbox(
            "Model OpenRouter",
            list(OPENROUTER_FREE_MODEL_OPTIONS.keys()),
            index=_model_select_index(),
            help="Pilih model free OpenRouter. Untuk model lain, isi llm.model di secrets.toml lalu pilih Custom.",
        )
        selected_model = OPENROUTER_FREE_MODEL_OPTIONS[model_label]

        run_until_label = st.selectbox(
            "Jalankan sampai tahap",
            list(RUN_UNTIL_OPTIONS.keys()),
            index=list(RUN_UNTIL_OPTIONS.keys()).index(default_run_until),
        )

        force_from_start = st.checkbox(
            "Proses ulang dari awal",
            value=default_force_start,
            help="Abaikan cache lama dan mulai ulang dari raw dataset.",
        )

        force_from_step_enabled = st.checkbox(
            "Proses ulang dari tahap tertentu",
            value=default_force_step_enabled,
            disabled=force_from_start,
            help="Tahap sebelumnya tetap boleh memakai cache jika dataset sama.",
        )

        force_from_step_label = None
        if force_from_step_enabled and not force_from_start:
            step_labels = [
                "Opinion units (02)",
                "POS tagging Stanza (02c)",
                "Candidate codes (03)",
                "Normalisasi candidate_code (05)",
                "Candidate summary normalisasi (06)",
            ]
            force_from_step_label = st.selectbox(
                "Mulai ulang dari",
                step_labels,
                index=step_labels.index(default_force_step_label) if default_force_step_label in step_labels else 2,
            )
        else:
            st.caption("Auto-resume aktif jika raw dataset sama dengan hasil lama.")

        col1, col2 = st.columns(2)
        with col1:
            retry_only_error = st.checkbox(
                "Retry hanya baris error opinion_units",
                value=True,
                disabled=force_from_start or (force_from_step_enabled and force_from_step_label == "Opinion units (02)"),
            )
            if force_from_start or (force_from_step_enabled and force_from_step_label == "Opinion units (02)"):
                retry_only_error = False
            max_rows = st.number_input(
                "Batas baris diproses",
                min_value=0,
                max_value=100000,
                value=default_max_rows,
                step=1,
                help="Isi 0 untuk semua baris.",
            )
            stanza_lang = st.text_input("Bahasa Stanza", value="id")
            auto_download_stanza = st.checkbox("Download model Stanza otomatis", value=True)

        with col2:
            always_retry = st.checkbox("Retry otomatis saat provider error", value=LLM_ALWAYS_RETRY_DEFAULT)
            retry_per_call = st.number_input(
                "Jumlah retry per request",
                min_value=0,
                max_value=50,
                value=0,
                step=1,
                disabled=always_retry,
            )
            timeout_seconds = st.number_input(
                "Timeout request LLM",
                min_value=30,
                max_value=1200,
                value=180,
                step=30,
            )
            save_raw_responses = st.checkbox("Simpan response mentah LLM", value=False)

        st.caption(f"Model yang dipakai: `{selected_model}`")

    force_from_step = ""
    if force_from_step_enabled and not force_from_start:
        if force_from_step_label == "Opinion units (02)":
            force_from_step = "opinion_units"
        elif force_from_step_label == "POS tagging Stanza (02c)":
            force_from_step = "pos_tagging"
        elif force_from_step_label == "Candidate codes (03)":
            force_from_step = "candidate_codes"
        elif force_from_step_label == "Normalisasi candidate_code (05)":
            force_from_step = "candidate_normalization"
        elif force_from_step_label == "Candidate summary normalisasi (06)":
            force_from_step = "candidate_summary"

    return {
        "model_id": selected_model,
        "force_all_comparative": force_all_comparative,
        "run_until": RUN_UNTIL_OPTIONS[run_until_label],
        "force_from_start": bool(force_from_start),
        "force_from_step_enabled": bool(force_from_step_enabled and not force_from_start),
        "force_from_step": force_from_step,
        "retry_only_error": bool(retry_only_error and not force_from_start),
        "max_rows": int(max_rows),
        "stanza_lang": str(stanza_lang).strip() or "id",
        "auto_download_stanza": bool(auto_download_stanza),
        "use_raw_dataset_cache": not bool(force_from_start),
        "always_retry": bool(always_retry),
        "retry_per_call": int(retry_per_call),
        "timeout_seconds": int(timeout_seconds),
        "save_raw_responses": bool(save_raw_responses),
        "preset": preset,
    }


def _read_output(project_dir: Path, filename: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
    return safe_read_csv(project_dir / filename, columns=columns)


def _count_rows(project_dir: Path, filename: str) -> int:
    path = project_dir / filename
    if not path.exists() or path.stat().st_size == 0:
        return 0
    try:
        return len(safe_read_csv(path))
    except Exception:
        return 0


def _normalization_health(mapping_df: pd.DataFrame) -> Tuple[str, str]:
    if mapping_df.empty or "normalization_action" not in mapping_df.columns:
        return "Belum tersedia", "quality-warn"
    actions = mapping_df["normalization_action"].astype(str).str.lower()
    changed = int(actions.isin(["merge", "rename", "specificize"]).sum())
    total = len(mapping_df)
    if total == 0 or changed == 0:
        return "Perlu cek: belum ada aspek yang berubah", "quality-bad"
    ratio = changed / max(total, 1)
    if ratio > 0.45:
        return "Perlu cek: penggabungan cukup agresif", "quality-warn"
    return f"Sehat: {changed} perubahan dari {total} aspek", "quality-ok"


def _pipeline_output_statuses(project_dir: Path) -> Dict[str, str]:
    outputs = {
        "raw_dataset": ("01_raw_dataset.csv", None),
        "opinion_units": ("02_opinion_units.csv", "02_errors.csv"),
        "pos_tagging": ("02c_opinion_units_pos.csv", "02c_pos_errors.csv"),
        "candidate_codes": ("03_candidate_codes.csv", "03_candidate_errors.csv"),
        "candidate_normalization": (
            "05_candidate_code_normalized.csv",
            "05_candidate_normalization_errors.csv",
        ),
        "candidate_summary": ("06_candidate_summary_normalized.csv", None),
    }
    statuses: Dict[str, str] = {}
    for step, (output_name, error_name) in outputs.items():
        output_path = project_dir / output_name
        if output_path.exists():
            statuses[step] = "ok"
        elif error_name and _count_rows(project_dir, error_name):
            statuses[step] = "error"
        else:
            statuses[step] = "pending"
    return statuses


def _llm_usage_summary(project_dir: Path) -> Dict[str, float]:
    summary = {"calls": 0.0, "tokens": 0.0, "seconds": 0.0, "cache_hits": 0.0}
    path = project_dir / "raw_llm_responses.jsonl"
    if not path.exists():
        return summary
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                usage = record.get("usage") or {}
                summary["calls"] += 1
                summary["tokens"] += float(usage.get("total_tokens") or 0)
                summary["seconds"] += float(usage.get("elapsed_seconds") or 0)
                summary["cache_hits"] += float(bool(usage.get("cache_hit")))
    except OSError:
        return summary
    return summary


def _load_quality_report(project_dir: Path) -> Dict[str, Any]:
    path = project_dir / "05_candidate_normalization_quality_report.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def render_paginated_dataframe(
    df: pd.DataFrame,
    *,
    key: str,
    label: str = "",
    default_page_size: int = 25,
    page_size_options: Optional[List[int]] = None,
) -> None:
    if df.empty:
        st.info("Belum ada data untuk ditampilkan.")
        return

    page_size_options = page_size_options or [10, 25, 50, 100, 200]
    if default_page_size not in page_size_options:
        default_page_size = page_size_options[0]

    search = st.text_input(
        f"Filter {label or 'tabel'}",
        key=f"{key}_filter",
        placeholder="Cari teks di semua kolom...",
    ).strip()
    visible_df = df
    if search:
        matches = df.astype(str).apply(
            lambda column: column.str.contains(search, case=False, na=False, regex=False)
        )
        visible_df = df.loc[matches.any(axis=1)]

    total_rows = len(visible_df)
    if total_rows == 0:
        suffix = f" dari {len(df):,}" if search else ""
        st.caption(f"{label or 'Tabel'}: 0{suffix} baris")
        st.info("Tidak ada baris yang cocok dengan filter.")
        return

    top_left, top_mid, top_right = st.columns([1.3, 1, 1.2])
    with top_left:
        suffix = f" dari {len(df):,}" if search else ""
        st.caption(f"{label or 'Tabel'}: {total_rows:,}{suffix} baris")
    with top_mid:
        page_size = st.selectbox(
            "Baris per halaman",
            page_size_options,
            index=page_size_options.index(default_page_size),
            key=f"{key}_page_size",
        )

    total_pages = max(1, (total_rows + int(page_size) - 1) // int(page_size))
    current_page_key = f"{key}_page"
    current_page = int(st.session_state.get(current_page_key, 1))
    current_page = min(max(1, current_page), total_pages)
    if st.session_state.get(current_page_key) != current_page:
        st.session_state[current_page_key] = current_page

    with top_right:
        current_page = st.number_input(
            "Halaman",
            min_value=1,
            max_value=total_pages,
            step=1,
            key=current_page_key,
        )

    start = (int(current_page) - 1) * int(page_size)
    end = min(start + int(page_size), total_rows)
    st.caption(f"Menampilkan baris {start + 1:,}-{end:,} dari {total_rows:,}.")
    st.dataframe(visible_df.iloc[start:end], width="stretch")


def _render_output_downloads(project_dir: Path) -> None:
    files = [
        ("Validasi input", "01_entity_validation.csv"),
        ("Ringkasan akhir", "06_candidate_summary_normalized.csv"),
        ("Mapping normalisasi", "05_candidate_code_mapping.csv"),
        ("Candidate code normalized", "05_candidate_code_normalized.csv"),
        ("Ringkasan awal", "04_candidate_summary.csv"),
        ("Candidate codes", "03_candidate_codes.csv"),
        ("Opinion units", "02_opinion_units.csv"),
        ("Raw dataset", "01_raw_dataset.csv"),
        ("Manifest run", "manifest.json"),
    ]
    available = [(label, filename) for label, filename in files if (project_dir / filename).exists()]
    if not available:
        return

    with st.expander("Download file tertentu"):
        st.caption("Pilih satu artefak jika tidak memerlukan seluruh hasil dalam bentuk ZIP.")
        columns = st.columns(2)
        for index, (label, filename) in enumerate(available):
            path = project_dir / filename
            mime = "application/json" if path.suffix.lower() == ".json" else "text/csv"
            with columns[index % 2]:
                st.download_button(
                    f"Download {label}",
                    data=path.read_bytes(),
                    file_name=filename,
                    mime=mime,
                    key=f"download_{project_dir.name}_{filename}",
                    width="stretch",
                )


def _manual_edit_audit_path(project_dir: Path) -> Path:
    return project_dir / "manual_candidate_code_edits.jsonl"


def _append_manual_edit_audit(project_dir: Path, payload: Dict[str, Any]) -> None:
    audit_path = _manual_edit_audit_path(project_dir)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def render_candidate_code_editor(project_dir: Path) -> None:
    summary_df = _read_output(project_dir, "06_candidate_summary_normalized.csv", NORMALIZED_SUMMARY_COLUMNS)
    mapping_df = _read_output(project_dir, "05_candidate_code_mapping.csv", NORMALIZATION_MAPPING_COLUMNS)
    normalized_df = _read_output(project_dir, "05_candidate_code_normalized.csv", NORMALIZED_COLUMNS)
    if summary_df.empty or mapping_df.empty or normalized_df.empty:
        ui.render_empty_state(
            "Editor candidate code belum tersedia",
            "Jalankan sampai normalisasi selesai agar tabel candidate code bisa diedit manual.",
        )
        return

    editor_df = summary_df.loc[:, ["normalized_candidate_code", "frequency", "sample_opinion_units"]].copy()
    editor_df.insert(0, "pilih", False)
    editor_df["action"] = editor_df["normalized_candidate_code"].astype(str)
    candidate_options = sorted(
        {str(code).strip() for code in summary_df["normalized_candidate_code"].fillna("").astype(str).tolist() if str(code).strip()}
    )
    action_options = candidate_options + ["Buat candidate code baru"]
    st.caption("Ceklis baris yang ingin diubah, lalu pilih target candidate code di kolom Action.")
    edited_df = st.data_editor(
        editor_df,
        key=f"candidate_code_editor_{project_dir.name}",
        hide_index=True,
        width="stretch",
        num_rows="fixed",
        column_config={
            "pilih": st.column_config.CheckboxColumn("Pilih", help="Ceklis baris yang ingin diubah."),
            "normalized_candidate_code": st.column_config.TextColumn(
                "normalized_candidate_code",
                disabled=True,
            ),
            "frequency": st.column_config.NumberColumn(
                "frequency",
                disabled=True,
            ),
            "sample_opinion_units": st.column_config.TextColumn(
                "sample_opinion_units",
                disabled=True,
                width="large",
            ),
            "action": st.column_config.SelectboxColumn(
                "Action",
                options=action_options,
                required=True,
                help="Pilih candidate code tujuan. Jika belum ada, pilih buat baru.",
            ),
        },
        disabled=["normalized_candidate_code", "frequency", "sample_opinion_units"],
    )

    manual_code = st.text_input(
        "Nama candidate code baru",
        key=f"manual_candidate_code_{project_dir.name}",
        placeholder="Contoh: motif",
        help="Dipakai jika Action memilih 'Buat candidate code baru'.",
    ).strip()

    selected_rows = edited_df[edited_df["pilih"].astype(bool)].copy()
    if st.button("Terapkan perubahan manual", type="primary", width="stretch"):
        if selected_rows.empty:
            st.warning("Pilih minimal satu baris dulu.")
            return

        edit_rows: list[dict[str, Any]] = []
        working_mapping = mapping_df.copy()
        working_normalized = normalized_df.copy()
        for row in selected_rows.to_dict(orient="records"):
            source_code = str(row.get("normalized_candidate_code", "")).strip()
            action = str(row.get("action", "")).strip()
            if not source_code or not action:
                continue
            if action == "Buat candidate code baru":
                if not manual_code:
                    st.error("Isi nama candidate code baru dulu.")
                    return
                target_code = manual_code
                action_label = "manual_create"
            else:
                target_code = action
                action_label = "manual_merge" if target_code != source_code else "keep"

            if not target_code:
                continue

            if source_code == target_code:
                continue

            source_mask_norm = working_normalized["normalized_candidate_code"].astype(str) == source_code
            source_mask_map = working_mapping["normalized_candidate_code"].astype(str) == source_code
            working_normalized.loc[source_mask_norm, "normalized_candidate_code"] = target_code
            working_normalized.loc[source_mask_norm, "normalization_action"] = action_label
            working_normalized.loc[source_mask_norm, "normalization_reason"] = "Diperbarui manual oleh pengguna."
            working_normalized.loc[source_mask_norm, "normalization_confidence"] = "manual"

            working_mapping.loc[source_mask_map, "normalized_candidate_code"] = target_code
            working_mapping.loc[source_mask_map, "normalization_action"] = action_label
            working_mapping.loc[source_mask_map, "normalization_reason"] = "Diperbarui manual oleh pengguna."
            working_mapping.loc[source_mask_map, "normalization_confidence"] = "manual"

            edit_rows.append(
                {
                    "source_candidate_code": source_code,
                    "target_candidate_code": target_code,
                    "action": action_label,
                    "selected": True,
                }
            )

        if not edit_rows:
            st.info("Tidak ada perubahan yang perlu diterapkan.")
            return

        working_normalized = working_normalized.reindex(columns=NORMALIZED_COLUMNS)
        save_df(working_mapping.reindex(columns=NORMALIZATION_MAPPING_COLUMNS), project_dir / "05_candidate_code_mapping.csv")
        save_df(working_normalized, project_dir / "05_candidate_code_normalized.csv")
        refreshed_summary = build_normalized_candidate_summary(working_normalized, project_dir=project_dir, force=True)
        _append_manual_edit_audit(
            project_dir,
            {
                "ts": datetime.now().isoformat(timespec="seconds"),
                "project_dir": str(project_dir),
                "changes": edit_rows,
            },
        )
        try:
            storage.refresh_run_outputs(LOCAL_RESULTS_DIR, project_dir)
        except Exception:
            pass
        st.success(f"{len(edit_rows)} perubahan candidate code sudah disimpan.")
        st.caption(
            f"Ringkasan baru berisi {len(refreshed_summary)} candidate code ternormalisasi."
        )
        st.rerun()


def show_outputs(project_dir: Path) -> None:
    raw_n = _count_rows(project_dir, "01_raw_dataset.csv")
    validation_df = _read_output(project_dir, "01_entity_validation.csv")
    rejected_input_n = 0
    if not validation_df.empty and "validation_status" in validation_df.columns:
        rejected_input_n = int(
            validation_df["validation_status"].astype(str).eq("rejected").sum()
        )
    op_n = _count_rows(project_dir, "02_opinion_units.csv")
    cand_n = _count_rows(project_dir, "03_candidate_codes.csv")
    summary_n = _count_rows(project_dir, "04_candidate_summary.csv")
    mapping_df = _read_output(project_dir, "05_candidate_code_mapping.csv", NORMALIZATION_MAPPING_COLUMNS)
    normalized_summary_n = _count_rows(project_dir, "06_candidate_summary_normalized.csv")
    error_n = (
        _count_rows(project_dir, "02_errors.csv")
        + _count_rows(project_dir, "02c_pos_errors.csv")
        + _count_rows(project_dir, "03_candidate_errors.csv")
        + _count_rows(project_dir, "05_candidate_normalization_errors.csv")
    )

    ui.render_status_stepper(_pipeline_output_statuses(project_dir))

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Pertanyaan lolos", raw_n)
    m2.metric("Ditolak awal", rejected_input_n)
    m3.metric("Opinion unit", op_n)
    m4.metric("Aspek mentah", summary_n or cand_n)
    m5.metric("Aspek akhir", normalized_summary_n)
    m6.metric("Error", error_n)

    usage = _llm_usage_summary(project_dir)
    usage_a, usage_b, usage_c = st.columns(3)
    usage_a.metric("Panggilan LLM tercatat", int(usage["calls"]))
    usage_b.metric("Token tercatat", f"{int(usage['tokens']):,}")
    usage_c.metric("Waktu respons LLM", f"{usage['seconds']:.1f} dtk")

    health_text, health_class = _normalization_health(mapping_df)
    changed_count = 0
    if not mapping_df.empty and "normalization_action" in mapping_df.columns:
        actions = mapping_df["normalization_action"].astype(str).str.lower()
        changed_count = int(actions.isin(["merge", "rename", "specificize"]).sum())
    reduction_text = "belum tersedia"
    if summary_n and normalized_summary_n:
        reduction_text = f"{summary_n} aspek mentah menjadi {normalized_summary_n} aspek akhir"
    st.markdown(
        f"""
        <div class="insight-panel">
            <strong>Kualitas normalisasi:</strong> <span class="{health_class}">{health_text}</span><br>
            <span>{reduction_text}. Perubahan label terdeteksi: {changed_count}. Error tercatat: {error_n}.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    quality_report = _load_quality_report(project_dir)
    generic_heads = quality_report.get("generic_heads_detected") or []
    relabel = quality_report.get("overmerge_relabel") or quality_report.get("relabel") or {}
    st.markdown("**Pemeriksaan kualitas**")
    quality_a, quality_b, quality_c = st.columns(3)
    quality_a.metric(
        "Generic heads",
        len(generic_heads) if isinstance(generic_heads, list) else 0,
    )
    quality_b.metric(
        "Relabel overmerge",
        len(relabel) if isinstance(relabel, (list, dict)) else int(bool(relabel)),
    )
    quality_c.metric("Baris error", error_n)
    if error_n:
        st.warning(
            "Ada baris yang gagal diproses. Buka tab Diagnostik & error sebelum memakai hasil akhir."
        )
    elif generic_heads:
        st.warning(
            "Normalisasi mendeteksi kepala label yang terlalu generik. Tinjau mapping step 05."
        )
    elif mapping_df.empty:
        st.info("Laporan normalisasi belum tersedia untuk run ini.")
    else:
        st.success("Tidak ada peringatan kualitas utama yang tercatat pada run ini.")

    final_summary = _read_output(project_dir, "06_candidate_summary_normalized.csv", NORMALIZED_SUMMARY_COLUMNS)
    early_summary = _read_output(project_dir, "04_candidate_summary.csv", SUMMARY_COLUMNS)
    candidate_df = _read_output(project_dir, "03_candidate_codes.csv", CANDIDATE_COLUMNS)
    opinion_df = _read_output(project_dir, "02_opinion_units.csv", OUTPUT_COLUMNS)

    tabs = st.tabs([
        "Ringkasan akhir",
        "Aspek sebelum/sesudah",
        "Edit candidate code",
        "Data pendapat",
        "Diagnostik & error",
    ])

    with tabs[0]:
        if not final_summary.empty:
            render_paginated_dataframe(final_summary, key="final_summary", label="Ringkasan akhir", default_page_size=25)
        elif not early_summary.empty:
            st.info("Ringkasan normalisasi belum tersedia. Menampilkan ringkasan awal.")
            render_paginated_dataframe(early_summary, key="early_summary_fallback", label="Ringkasan awal", default_page_size=25)
        else:
            st.info("Ringkasan belum tersedia.")

    with tabs[1]:
        if not mapping_df.empty:
            changed_mapping = mapping_df.copy()
            if {
                "original_candidate_code",
                "normalized_candidate_code",
            }.issubset(changed_mapping.columns):
                changed_mapping = changed_mapping.loc[
                    changed_mapping["original_candidate_code"].astype(str)
                    != changed_mapping["normalized_candidate_code"].astype(str)
                ]
            st.markdown("**Perubahan label pada step 05**")
            if changed_mapping.empty:
                st.info("Tidak ada perubahan label pada mapping normalisasi ini.")
            else:
                render_paginated_dataframe(
                    changed_mapping,
                    key="mapping_diff",
                    label="Perubahan sebelum dan sesudah normalisasi",
                    default_page_size=25,
                )
            with st.expander("Lihat seluruh mapping normalisasi"):
                render_paginated_dataframe(
                    mapping_df,
                    key="mapping_all",
                    label="Seluruh mapping",
                    default_page_size=25,
                )
        else:
            st.info("Belum ada mapping normalisasi.")
        with st.expander("Lihat ringkasan aspek sebelum normalisasi"):
            if not early_summary.empty:
                render_paginated_dataframe(
                    early_summary,
                    key="early_summary",
                    label="Aspek sebelum normalisasi",
                    default_page_size=25,
                )
            else:
                st.info("Belum ada candidate_summary awal.")

    with tabs[2]:
        render_candidate_code_editor(project_dir)

    with tabs[3]:
        data_tabs = st.tabs(
            [
                "Aspek per opinion unit",
                "Opinion units",
                "Raw dataset",
                "Validasi input",
            ]
        )
        with data_tabs[0]:
            if not candidate_df.empty:
                render_paginated_dataframe(candidate_df, key="candidate_codes", label="Aspek per opinion unit", default_page_size=25)
            else:
                st.info("Belum ada candidate_codes.")
        with data_tabs[1]:
            if not opinion_df.empty:
                render_paginated_dataframe(opinion_df, key="opinion_units", label="Opinion units", default_page_size=25)
            else:
                st.info("Belum ada opinion_units.")
        with data_tabs[2]:
            raw_df = _read_output(project_dir, "01_raw_dataset.csv")
            if not raw_df.empty:
                render_paginated_dataframe(raw_df, key="raw_dataset", label="Raw dataset", default_page_size=25)
            else:
                st.info("Belum ada raw dataset.")
        with data_tabs[3]:
            if not validation_df.empty:
                render_paginated_dataframe(
                    validation_df,
                    key="entity_validation",
                    label="Validasi hal yang dibandingkan",
                    default_page_size=25,
                )
            else:
                st.info("Run lama ini belum memiliki laporan validasi input.")

    with tabs[4]:
        if quality_report:
            st.markdown("**Panel kualitas normalisasi**")
            if generic_heads:
                st.write("Generic heads terdeteksi:", generic_heads)
            with st.expander("Detail laporan kualitas"):
                st.json(quality_report)

        error_tabs = st.tabs(["Ringkasan file", "Opinion error", "POS error", "Candidate error", "Normalisasi error"])
        status_rows = []
        for filename, label in [
            ("01_entity_validation.csv", "Validasi input"),
            ("01_raw_dataset.csv", "Raw dataset"),
            ("02_opinion_units.csv", "Opinion units"),
            ("02c_opinion_units_pos.csv", "POS tagging"),
            ("03_candidate_codes.csv", "Candidate codes"),
            ("04_candidate_summary.csv", "Candidate summary awal"),
            ("05_candidate_code_mapping.csv", "Mapping normalisasi"),
            ("05_candidate_code_normalized.csv", "Candidate codes normalized"),
            ("06_candidate_summary_normalized.csv", "Candidate summary akhir"),
        ]:
            status_rows.append({"output": label, "file": filename, "rows": _count_rows(project_dir, filename)})
        with error_tabs[0]:
            render_paginated_dataframe(pd.DataFrame(status_rows), key="file_status", label="Ringkasan file", default_page_size=25)
        for tab, filename in zip(error_tabs[1:], ["02_errors.csv", "02c_pos_errors.csv", "03_candidate_errors.csv", "05_candidate_normalization_errors.csv"]):
            with tab:
                df = _read_output(project_dir, filename)
                if not df.empty:
                    error_key = Path(filename).stem.replace(".", "_")
                    render_paginated_dataframe(df, key=f"error_{error_key}", label=filename, default_page_size=25)
                else:
                    st.info("Tidak ada error tercatat.")

    _render_output_downloads(project_dir)
    zip_bytes = make_result_zip(project_dir)
    st.download_button(
        "Download semua hasil",
        data=zip_bytes,
        file_name=f"hasil_analisis_aspek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        mime="application/zip",
        width="stretch",
    )


def list_result_projects() -> List[Tuple[str, Path]]:
    try:
        storage.init_database(LOCAL_RESULTS_DIR)
        search_root = LOCAL_RESULTS_DIR / "projects"
        if search_root.exists():
            for project_dir in search_root.iterdir():
                if project_dir.is_dir() and (project_dir / "manifest.json").exists():
                    storage.refresh_run_outputs(LOCAL_RESULTS_DIR, project_dir)

        db_runs = storage.list_runs(LOCAL_RESULTS_DIR)
        projects_from_db: List[Tuple[datetime, str, Path]] = []
        for run in db_runs:
            project_dir = Path(str(run.get("project_dir", "")))
            if not project_dir.exists():
                continue
            updated_raw = run.get("updated_at") or run.get("created_at") or ""
            try:
                updated_at = datetime.fromisoformat(str(updated_raw))
            except Exception:
                updated_at = datetime.min
            signature = str(run.get("signature") or project_dir.name)
            status_text = str(run.get("status") or "unknown")
            model_text = str(run.get("model") or "-")
            settings_json = run.get("settings_json") or "{}"
            try:
                settings_obj = json.loads(str(settings_json))
            except Exception:
                settings_obj = {}
            manifest = load_manifest(project_dir)
            project_title = str(
                settings_obj.get("project_title")
                or (manifest.get("project_title") if isinstance(manifest, dict) else "")
                or project_dir.name
            )
            label = (
                f"{updated_at.strftime('%Y-%m-%d %H:%M')} | "
                f"{project_title} | "
                f"{status_text} | "
                f"{int(run.get('raw_rows') or 0)} baris | "
                f"{int(run.get('normalized_candidate_codes') or run.get('raw_candidate_codes') or 0)} aspek | "
                f"{model_text} | {signature[:10]}"
            )
            projects_from_db.append((updated_at, label, project_dir))
        if projects_from_db:
            projects_from_db.sort(key=lambda item: item[0], reverse=True)
            return [(label, path) for _, label, path in projects_from_db]
    except Exception:
        pass

    if not LOCAL_RESULTS_DIR.exists():
        return []

    search_root = LOCAL_RESULTS_DIR / "projects"
    if not search_root.exists():
        search_root = LOCAL_RESULTS_DIR

    projects: List[Tuple[datetime, str, Path]] = []
    expected_outputs = [
        "01_raw_dataset.csv",
        "02_opinion_units.csv",
        "03_candidate_codes.csv",
        "04_candidate_summary.csv",
        "05_candidate_code_mapping.csv",
        "06_candidate_summary_normalized.csv",
    ]

    for project_dir in search_root.iterdir():
        if not project_dir.is_dir():
            continue
        if not (project_dir / "manifest.json").exists() and not any((project_dir / name).exists() for name in expected_outputs):
            continue

        manifest = load_manifest(project_dir)
        updated_raw = manifest.get("created_or_updated_at") or manifest.get("created_at") or ""
        try:
            updated_at = datetime.fromisoformat(str(updated_raw))
        except Exception:
            try:
                updated_at = datetime.fromtimestamp(project_dir.stat().st_mtime)
            except Exception:
                updated_at = datetime.min

        raw_rows = _count_rows(project_dir, "01_raw_dataset.csv")
        final_codes = _count_rows(project_dir, "06_candidate_summary_normalized.csv")
        candidate_codes = _count_rows(project_dir, "04_candidate_summary.csv")
        signature = manifest.get("signature") or project_dir.name
        status_text = str(manifest.get("status") or "tersimpan")
        model_text = str(manifest.get("model") or "-")
        project_title = str(manifest.get("project_title") or manifest.get("settings", {}).get("project_title") or project_dir.name)
        short_sig = str(signature)[:10]
        label = (
            f"{updated_at.strftime('%Y-%m-%d %H:%M')} | "
            f"{project_title} | "
            f"{status_text} | {raw_rows} baris | "
            f"{final_codes or candidate_codes} aspek | {model_text} | {short_sig}"
        )
        projects.append((updated_at, label, project_dir))

    projects.sort(key=lambda item: item[0], reverse=True)
    return [(label, path) for _, label, path in projects]


def render_results_page() -> None:
    ui.inject_custom_css()
    ui.render_sidebar(LLM_API_KEY, LLM_MODEL, LOCAL_RESULTS_DIR, active="results")
    ui.render_results_header()

    with st.spinner("Memuat daftar run tersimpan..."):
        projects = list_result_projects()
    if not projects:
        ui.render_empty_state(
            "Belum ada hasil analisis",
            "Jalankan analisis pertama dari halaman Run Analisis. Hasil yang selesai akan muncul otomatis di sini.",
        )
        st.page_link("pages/1_Run_Analisis.py", label="Buka Run Analisis")
        return

    ui.render_section_title(
        1,
        "Pilih Run",
        "Cari berdasarkan tanggal, status, model, atau signature. Run terbaru ditampilkan di atas.",
    )
    filter_left, filter_right = st.columns([2, 1])
    with filter_left:
        run_search = st.text_input(
            "Cari run",
            placeholder="Contoh: completed, gpt-oss, 14258a...",
        ).strip().lower()
    statuses = sorted(
        {
            label.split("|")[2].strip()
            for label, _ in projects
            if len(label.split("|")) > 2
        }
    )
    with filter_right:
        status_filter = st.selectbox("Status", ["Semua"] + statuses)

    filtered_projects = []
    for label, path in projects:
        label_status = label.split("|")[2].strip() if len(label.split("|")) > 2 else ""
        matches_search = not run_search or run_search in label.lower() or run_search in str(path).lower()
        matches_status = status_filter == "Semua" or label_status == status_filter
        if matches_search and matches_status:
            filtered_projects.append((label, path))

    if not filtered_projects:
        ui.render_empty_state(
            "Run tidak ditemukan",
            "Ubah kata pencarian atau pilih status lain untuk menampilkan run tersimpan.",
        )
        return

    labels = [label for label, _ in filtered_projects]
    paths = [path for _, path in filtered_projects]
    last_project = st.session_state.get("last_project_dir", "")
    default_index = 0
    if last_project:
        for idx, path in enumerate(paths):
            if str(path) == str(last_project):
                default_index = idx
                break

    selected_label = st.selectbox("Pilih hasil analisis", labels, index=default_index)
    selected_project = paths[labels.index(selected_label)]
    st.caption(f"Folder: `{selected_project}`")
    ui.render_section_title(2, "Ringkasan dan Tabel", "Mulai dari ringkasan akhir, lalu buka tab lain untuk audit aspek, edit label manual, opinion unit, dan error.")
    show_outputs(selected_project)


def render_run_completion(project_dir: Path, *, status: str = "completed") -> None:
    st.session_state["last_project_dir"] = str(project_dir)
    try:
        storage.refresh_run_outputs(LOCAL_RESULTS_DIR, project_dir, status=status)
    except Exception as db_error:
        st.warning(f"Hasil tersimpan, tetapi indeks database belum terbarui: {db_error}")

    if status == "failed":
        st.error("Proses berhenti karena error. Output sementara tetap bisa dicek di halaman Hasil.")
    else:
        st.success("Analisis selesai. Hasil lengkap tersedia di halaman Hasil.")
    st.caption(f"Folder hasil: `{project_dir}`")
    try:
        st.page_link("pages/2_Hasil.py", label="Buka halaman Hasil")
    except Exception:
        st.info("Buka menu halaman di sidebar, lalu pilih Hasil.")


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    ui.inject_custom_css()
    ui.render_sidebar(LLM_API_KEY, LLM_MODEL, LOCAL_RESULTS_DIR, active="run")
    ui.render_app_header()
    ui.render_onboarding()
    ui.render_pipeline_overview()

    ui.render_section_title(
        1,
        "Upload Data",
        "Gunakan CSV berisi pasangan pertanyaan dan jawaban. Kolom akan dideteksi otomatis, tetapi tetap bisa dikoreksi manual.",
    )

    uploaded_file = st.file_uploader("Upload CSV tanya-jawab", type=["csv"])
    if uploaded_file is None:
        ui.render_empty_state(
            "Siapkan CSV untuk memulai",
            "File minimal memiliki satu kolom pertanyaan dan satu kolom jawaban. "
            "Setelah diunggah, sistem akan membantu mendeteksi kedua kolom tersebut.",
        )
        st.page_link("pages/2_Hasil.py", label="Lihat hasil yang sudah tersimpan")
        return

    try:
        preview_df = load_csv_flexible(uploaded_file)
        detected_q_col, detected_a_col = detect_question_answer_columns(preview_df)
        st.success("CSV berhasil dibaca.")
        stat_a, stat_b, stat_c = st.columns(3)
        stat_a.metric("Baris", len(preview_df))
        stat_b.metric("Kolom", len(preview_df.columns))
        stat_c.metric("Preview", min(20, len(preview_df)))
        st.markdown(
            '<div class="upload-note">Periksa kolom yang akan dianalisis. Jika deteksi otomatis belum tepat, pilih kolom pertanyaan dan jawaban yang benar sebelum menjalankan proses.</div>',
            unsafe_allow_html=True,
        )
        col_q, col_a = st.columns(2)
        columns = list(preview_df.columns)
        with col_q:
            q_col = st.selectbox(
                "Kolom pertanyaan",
                columns,
                index=columns.index(detected_q_col) if detected_q_col in columns else 0,
            )
        with col_a:
            a_col = st.selectbox(
                "Kolom jawaban",
                columns,
                index=columns.index(detected_a_col) if detected_a_col in columns else min(1, len(columns) - 1),
            )
        with st.expander("Lihat preview CSV"):
            st.dataframe(preview_df.head(20), width="stretch")
    except Exception as e:
        st.error("CSV belum bisa dibaca.")
        st.caption(f"Detail teknis: {e}")
        st.info(
            "Pastikan file benar-benar berformat CSV, memiliki header kolom, "
            "dan tidak sedang rusak atau terkunci aplikasi lain."
        )
        return

    ui.render_section_title(
        2,
        "Judul Analisis",
        "Beri nama run agar folder hasil mudah dicari saat melihat banyak project tersimpan.",
    )
    default_title = Path(uploaded_file.name).stem if getattr(uploaded_file, "name", "") else "analisis"
    project_title = st.text_input(
        "Judul project",
        value=default_title,
        help="Nama ini akan masuk ke folder project dan membantu membedakan hasil run satu dengan yang lain.",
    ).strip() or default_title

    ui.render_section_title(
        3,
        "Tentukan Hal yang Dibandingkan",
        "Tuliskan objek, produk, kelompok, metode, atau pilihan yang memang dibandingkan "
        "dalam pertanyaan.",
    )
    st.markdown(
        '<div class="upload-note"><strong>Apa maksudnya?</strong> '
        'Isi nama hal yang ingin dibandingkan. Contoh: <b>batik tulis</b> dan '
        '<b>batik cap</b>. Jika pertanyaan memakai nama singkat, masukkan sebagai '
        'nama lain.</div>',
        unsafe_allow_html=True,
    )
    entity_input_df = render_comparison_entity_input()
    comparison_entities: List[ComparisonEntity] = []
    entity_setup_error = ""
    try:
        comparison_entities = parse_comparison_entities(entity_input_df)
        validate_entity_setup(comparison_entities)
        st.success(
            f"{len(comparison_entities)} hal yang dibandingkan siap diperiksa."
        )
    except ValueError as entity_error:
        entity_setup_error = str(entity_error)
        st.info(entity_setup_error)

    settings = render_advanced_settings()
    settings["project_title"] = project_title
    st.markdown("### Mulai Analisis")
    if entity_setup_error:
        st.error(entity_setup_error)
    else:
        st.info(
            "Pemeriksaan entity dan bentuk pertanyaan berjalan otomatis setelah Anda menekan tombol mulai."
        )
    run_clicked = st.button(
        "Mulai Analisis",
        type="primary",
        width="stretch",
        disabled=bool(entity_setup_error),
    )

    if not run_clicked:
        st.caption("Folder hasil baru dibuat setelah analisis dijalankan. Jika dataset yang sama sudah pernah diproses, sistem akan mencoba auto-resume.")
        return

    # Signature, folder project, dan manifest baru dibuat setelah tombol Mulai proses diklik.
    uploaded_file.seek(0)
    raw_bytes = uploaded_file.read()
    uploaded_file.seek(0)

    sig_settings = {
        "model": settings["model_id"],
        "project_title": project_title,
        "step_versions": STEP_VERSIONS,
        "prompt_hashes": prompt_hashes(),
        "force_all_comparative": settings["force_all_comparative"],
        "comparison_entities": [
            entity.as_dict() for entity in comparison_entities
        ],
        "max_rows": settings["max_rows"],
        "stanza_lang": settings.get("stanza_lang", "id"),
    }
    settings["comparison_entities"] = sig_settings["comparison_entities"]
    signature = dataset_signature(raw_bytes, sig_settings)
    project_dir = get_project_dir(signature, project_title)

    manifest = load_manifest(project_dir)
    manifest.update({
        "signature": signature,
        "project_title": project_title,
        "created_or_updated_at": datetime.now().isoformat(timespec="seconds"),
        "model": settings["model_id"],
        "base_url": LLM_BASE_URL,
        "step_versions": STEP_VERSIONS,
        "settings": settings,
    })
    write_manifest(project_dir, manifest)
    try:
        storage.upsert_run(
            LOCAL_RESULTS_DIR,
            signature=signature,
            project_dir=project_dir,
            status="running",
            model=settings["model_id"],
            run_until=settings["run_until"],
            preset=str(settings.get("preset", "")),
            settings=settings,
            step_versions=STEP_VERSIONS,
        )
        storage.add_event(LOCAL_RESULTS_DIR, signature, "Run dimulai.")
    except Exception as db_error:
        st.warning(f"Database belum bisa diperbarui: {db_error}")

    start_time = time.perf_counter()
    timer_box = st.empty()
    progress = st.progress(0)
    status = st.empty()
    with st.expander("Log teknis", expanded=False):
        log_box = st.empty()
    timer_stop_event, timer_thread = start_timer_watcher(timer_box, start_time)
    log_fn, update_timer_fn = make_live_logger(log_box=log_box, timer_box=timer_box, start_time=start_time)
    comparative_judger = make_comparative_judger(
        model_id=settings["model_id"],
        timeout_seconds=settings["timeout_seconds"],
        retry_per_call=settings["retry_per_call"],
        always_retry_per_call=settings["always_retry"],
        raw_log_path=project_dir / "raw_llm_responses.jsonl",
        log_fn=log_fn,
        update_timer_fn=update_timer_fn,
        bypass_cache=bool(settings.get("force_from_start", False)),
    )
    log_fn("Mulai proses.")
    log_fn(f"Provider: OpenRouter | model: {settings['model_id']}")
    log_fn(
        "Langkah 1: pencocokan entity oleh sistem, lalu pemeriksaan "
        "bentuk pertanyaan komparatif oleh LLM."
    )
    if settings.get("force_from_start"):
        log_fn("Mode rerun: paksa proses dari awal, cache lama diabaikan.")
    elif settings.get("force_from_step_enabled"):
        log_fn(f"Mode rerun: paksa proses mulai dari step {settings.get('force_from_step')}, step sebelumnya boleh diambil dari cache.")
    else:
        log_fn("Mode rerun: auto-resume dari local_results jika raw dataset sama.")

    try:
        status.write("Membangun 01_raw_dataset.csv...")
        log_fn("Membangun 01_raw_dataset.csv...")
        raw_df = build_raw_dataset(
            uploaded_file,
            max_rows=settings["max_rows"],
            project_dir=project_dir,
            force=bool(settings.get("force_from_start", False)),
            q_col=q_col,
            a_col=a_col,
            comparison_entities=comparison_entities,
            comparative_judger=comparative_judger,
            assume_comparative=settings["force_all_comparative"],
            log_fn=log_fn,
        )
        progress.progress(0.1)

        if settings["run_until"] == "raw_dataset":
            status.success("Selesai sampai 01_raw_dataset.csv.")
            log_fn("Selesai sampai 01_raw_dataset.csv.")
            progress.progress(1.0)
            render_run_completion(project_dir)
            return

        status.write("Membangun 02_opinion_units.csv...")
        log_fn("Membangun 02_opinion_units.csv...")

        cache_report = import_latest_outputs_from_same_raw_cache(
            raw_df,
            project_dir,
            enabled=bool(settings.get("use_raw_dataset_cache", True)),
            force_rerun=bool(settings.get("force_from_start", False)),
            comparison_entities=settings["comparison_entities"],
            log_fn=log_fn,
        )
        if cache_report.get("imported"):
            log_fn("Cache raw dataset dipakai: " + "; ".join(cache_report.get("imported", [])))
        else:
            skipped = "; ".join(cache_report.get("skipped", [])) or "tidak ada output yang bisa diimport"
            log_fn(f"Cache raw dataset tidak dipakai: {skipped}")

        # Jika tidak dipaksa, output dari cache akan membuat step skip otomatis.
        force_step = settings.get("force_from_step", "") if settings.get("force_from_step_enabled") else ""
        opinion_force = bool(settings.get("force_from_start")) or force_step == "opinion_units"
        pos_force = bool(settings.get("force_from_start")) or force_step in {"opinion_units", "pos_tagging"}
        candidate_force = bool(settings.get("force_from_start")) or force_step in {"opinion_units", "pos_tagging", "candidate_codes"}
        normalization_force = bool(settings.get("force_from_start")) or force_step in {"opinion_units", "pos_tagging", "candidate_codes", "candidate_normalization"}
        summary_force = bool(settings.get("force_from_start")) or force_step in {"opinion_units", "pos_tagging", "candidate_codes", "candidate_normalization", "candidate_summary"}

        if opinion_force:
            log_fn("Rerun aktif untuk 02_opinion_units.csv.")
        else:
            log_fn("02_opinion_units.csv akan dipakai dari cache/current project jika sudah ada.")

        opinion_df, error_df = step_opinion_units(
            raw_df,
            project_dir=project_dir,
            model_id=settings["model_id"],
            force_all_comparative=settings["force_all_comparative"],
            comparison_entities=comparison_entities,
            retry_per_call=settings["retry_per_call"],
            always_retry_per_call=settings["always_retry"],
            timeout_seconds=settings["timeout_seconds"],
            retry_only_error=settings["retry_only_error"],
            force=opinion_force,
            save_raw_responses=settings["save_raw_responses"],
            progress_bar=progress,
            status_box=status,
            log_fn=log_fn,
            update_timer_fn=update_timer_fn,
        )
        if settings["run_until"] == "opinion_units":
            progress.progress(1.0)
            update_timer_fn()
            status.success("Selesai sampai 02_opinion_units.csv.")
            log_fn("Selesai sampai 02_opinion_units.csv.")
            render_run_completion(project_dir)
            return

        status.write("Membangun 02c_opinion_units_pos.csv dengan Stanza...")
        log_fn("Membangun 02c_opinion_units_pos.csv dengan Stanza...")
        pos_df, pos_error_df = step_pos_tagging(
            opinion_df,
            project_dir=project_dir,
            stanza_lang=settings["stanza_lang"],
            auto_download_stanza=settings["auto_download_stanza"],
            force=pos_force,
            progress_bar=progress,
            status_box=status,
            log_fn=log_fn,
            update_timer_fn=update_timer_fn,
        )

        if settings["run_until"] == "pos_tagging":
            progress.progress(1.0)
            update_timer_fn()
            status.success("Selesai sampai 02c_opinion_units_pos.csv.")
            log_fn("Selesai sampai 02c_opinion_units_pos.csv.")
            render_run_completion(project_dir)
            return

        status.write("Membangun 03_candidate_codes.csv...")
        log_fn("Membangun 03_candidate_codes.csv...")
        if candidate_force:
            log_fn("Rerun aktif untuk 03_candidate_codes.csv.")
        else:
            log_fn("03_candidate_codes.csv akan dipakai dari cache/current project jika sudah ada.")
        candidate_df, candidate_error_df = step_candidate_codes(
            pos_df,
            project_dir=project_dir,
            model_id=settings["model_id"],
            retry_per_call=settings["retry_per_call"],
            always_retry_per_call=settings["always_retry"],
            timeout_seconds=settings["timeout_seconds"],
            force=candidate_force,
            save_raw_responses=settings["save_raw_responses"],
            progress_bar=progress,
            status_box=status,
            log_fn=log_fn,
            update_timer_fn=update_timer_fn,
        )

        if settings["run_until"] == "candidate_codes":
            progress.progress(1.0)
            update_timer_fn()
            status.success("Selesai sampai 03_candidate_codes.csv.")
            log_fn("Selesai sampai 03_candidate_codes.csv.")
            render_run_completion(project_dir)
            return

        status.write("Membangun 04_candidate_summary.csv...")
        log_fn("Membangun 04_candidate_summary.csv...")
        summary_df = build_candidate_summary(candidate_df, project_dir=project_dir, force=summary_force)
        log_fn(f"04_candidate_summary.csv selesai: {len(summary_df)} candidate_code unik sebelum normalisasi.")

        status.write("Membangun 05_candidate_code_normalized.csv...")
        log_fn("Membangun 05_candidate_code_normalized.csv...")
        normalized_df, mapping_df = step_candidate_normalization(
            candidate_df,
            summary_df,
            project_dir=project_dir,
            model_id=settings["model_id"],
            retry_per_call=settings["retry_per_call"],
            always_retry_per_call=settings["always_retry"],
            timeout_seconds=settings["timeout_seconds"],
            force=normalization_force,
            save_raw_responses=settings["save_raw_responses"],
            batch_size=25,
            progress_bar=progress,
            status_box=status,
            log_fn=log_fn,
            update_timer_fn=update_timer_fn,
        )
        log_fn(f"05_candidate_code_normalized.csv selesai: {len(mapping_df)} mapping candidate_code.")

        if settings["run_until"] == "candidate_normalization":
            progress.progress(1.0)
            update_timer_fn()
            status.success("Selesai sampai 05_candidate_code_normalized.csv.")
            log_fn("Selesai sampai 05_candidate_code_normalized.csv.")
            render_run_completion(project_dir)
            return

        status.write("Membangun 06_candidate_summary_normalized.csv...")
        log_fn("Membangun 06_candidate_summary_normalized.csv...")
        normalized_summary_df = build_normalized_candidate_summary(normalized_df, project_dir=project_dir, force=summary_force)
        log_fn(f"06_candidate_summary_normalized.csv selesai: {len(normalized_summary_df)} normalized candidate_code unik.")

        progress.progress(1.0)
        update_timer_fn()
        status.success("Proses selesai.")
        log_fn("Proses selesai.")
        render_run_completion(project_dir)

    except Exception as e:
        progress.progress(1.0)
        update_timer_fn()
        status.error("Proses berhenti karena error.")
        st.exception(e)
        if project_dir.exists():
            render_run_completion(project_dir, status="failed")
    finally:
        timer_stop_event.set()
        try:
            timer_thread.join(timeout=2)
        except Exception:
            pass
        timer_box.metric("Waktu proses", format_elapsed(time.perf_counter() - start_time))


if __name__ == "__main__":
    main()
