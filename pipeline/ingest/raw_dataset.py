"""Mechanical cleaning and step-01 raw dataset construction."""

import re
import unicodedata
from pathlib import Path
from typing import Any, BinaryIO

import pandas as pd

from pipeline.ingest.csv_io import load_csv_flexible, safe_read_csv, save_df
from pipeline.ingest.entity_validation import (
    ComparisonEntity,
    validate_comparative_rows,
)

RAW_COLUMNS = ["row_id", "question", "answer", "answer_python_cleaned"]


def mechanical_clean_text(text: Any) -> str:
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    value = unicodedata.normalize("NFKC", str(text))
    value = value.replace("\u200b", "").replace("\ufeff", "")
    value = re.sub(r"[\r\n\t]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r",{2,}", ",", value)
    value = re.sub(r"\.{2,}", ".", value)
    value = re.sub(r"!{2,}", "!", value)
    value = re.sub(r"\?{2,}", "?", value)
    value = re.sub(r"\s+([,.;:!?])", r"\1", value)
    value = re.sub(r"([,.;:!?])([^\s])", r"\1 \2", value)
    if value and value[-1] not in ".!?":
        value += "."
    return value


def detect_question_answer_columns(df: pd.DataFrame) -> tuple[str, str]:
    columns = list(df.columns)
    lower_map = {str(column).strip().lower(): column for column in columns}
    question_candidates = [
        "question",
        "questions",
        "pertanyaan",
        "q",
        "soal",
        "prompt",
        "item",
        "ask",
    ]
    answer_candidates = [
        "answer",
        "answers",
        "jawaban",
        "response",
        "responses",
        "respon",
        "tanggapan",
        "a",
    ]

    question_column = next(
        (lower_map[key] for key in question_candidates if key in lower_map),
        None,
    )
    answer_column = next(
        (lower_map[key] for key in answer_candidates if key in lower_map),
        None,
    )
    if question_column is None:
        question_column = next(
            (
                column
                for column in columns
                if "question" in str(column).lower() or "pertanyaan" in str(column).lower()
            ),
            None,
        )
    if answer_column is None:
        answer_column = next(
            (
                column
                for column in columns
                if any(
                    key in str(column).lower()
                    for key in ("answer", "jawaban", "response", "respon")
                )
            ),
            None,
        )
    if question_column is None or answer_column is None:
        if len(columns) < 2:
            raise RuntimeError("Tidak bisa mendeteksi kolom question-answer. CSV minimal perlu 2 kolom.")
        question_column = question_column or columns[0]
        answer_column = answer_column or columns[1]
    return str(question_column), str(answer_column)


def normalize_raw_dataset(
    df: pd.DataFrame,
    question_column: str,
    answer_column: str,
    max_rows: int = 0,
) -> pd.DataFrame:
    selected = df.head(max_rows).copy() if max_rows and max_rows > 0 else df.copy()
    row_id_column = next(
        (
            column
            for column in selected.columns
            if str(column).strip().lower()
            in {"row_id", "original_row_id", "original row id", "id_asli", "baris_asli"}
        ),
        None,
    )
    rows: list[dict[str, Any]] = []
    for index, row in selected.iterrows():
        question = "" if pd.isna(row.get(question_column, "")) else str(row.get(question_column, ""))
        answer = "" if pd.isna(row.get(answer_column, "")) else str(row.get(answer_column, ""))
        if row_id_column is not None and not pd.isna(row.get(row_id_column, None)):
            try:
                row_id = int(float(row.get(row_id_column)))
            except Exception:
                row_id = int(index) + 1
        else:
            row_id = int(index) + 1
        rows.append(
            {
                "row_id": row_id,
                "question": question.strip(),
                "answer": answer.strip(),
                "answer_python_cleaned": mechanical_clean_text(answer),
            }
        )
    return pd.DataFrame(rows)


def build_raw_dataset(
    uploaded_file: BinaryIO,
    *,
    max_rows: int,
    project_dir: Path,
    force: bool,
    q_col: str | None = None,
    a_col: str | None = None,
    comparison_entities: list[ComparisonEntity] | None = None,
    comparative_judger=None,
    assume_comparative: bool = False,
    log_fn=None,
) -> pd.DataFrame:
    raw_path = project_dir / "01_raw_dataset.csv"
    validation_path = project_dir / "01_entity_validation.csv"
    if raw_path.exists() and not force:
        return safe_read_csv(raw_path)
    frame = load_csv_flexible(uploaded_file)
    if not q_col or not a_col:
        q_col, a_col = detect_question_answer_columns(frame)
    raw_df = normalize_raw_dataset(frame, q_col, a_col, max_rows=max_rows)
    if comparison_entities:
        if not assume_comparative and comparative_judger is None:
            raise RuntimeError(
                "comparative_judger wajib disediakan untuk memeriksa bentuk pertanyaan."
            )
        raw_df, validation_report = validate_comparative_rows(
            raw_df,
            comparison_entities,
            comparative_judger=comparative_judger,
            assume_comparative=assume_comparative,
            log_fn=log_fn,
        )
        save_df(validation_report, validation_path)
        if raw_df.empty:
            raise RuntimeError(
                "Tidak ada pertanyaan yang lolos validasi hal yang dibandingkan."
            )
    save_df(raw_df, raw_path)
    return raw_df
