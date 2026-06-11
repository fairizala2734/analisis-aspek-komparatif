"""CSV input/output helpers with stable encoding behavior."""

from collections.abc import Sequence
from pathlib import Path
from typing import BinaryIO

import pandas as pd


def load_csv_flexible(uploaded_file: BinaryIO) -> pd.DataFrame:
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin1", "iso-8859-1"]
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding=encoding)
        except UnicodeDecodeError as exc:
            last_error = exc
        except Exception as exc:
            last_error = exc
            break
    uploaded_file.seek(0)
    try:
        return pd.read_csv(uploaded_file, encoding="utf-8", encoding_errors="replace")
    except Exception as exc:
        raise RuntimeError(f"Gagal membaca CSV. Error: {last_error or exc}") from exc


def safe_read_csv(path: Path, columns: Sequence[str] | None = None) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame(columns=list(columns or []))
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        return pd.read_csv(path)


def save_df(df: pd.DataFrame, path: Path) -> None:
    # Import lazily so ingest stays independent while every known pipeline output
    # is still checked at its write boundary.
    from pipeline.contracts import validate_frame

    validate_frame(path.name, df)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
