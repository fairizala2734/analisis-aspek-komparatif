import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


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
]


def utc_now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_database_path(local_results_dir: Path) -> Path:
    return local_results_dir / "app_data.sqlite3"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database(local_results_dir: Path) -> Path:
    db_path = get_database_path(local_results_dir)
    with connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                signature TEXT PRIMARY KEY,
                project_dir TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                model TEXT,
                run_until TEXT,
                preset TEXT,
                raw_rows INTEGER DEFAULT 0,
                opinion_units INTEGER DEFAULT 0,
                raw_candidate_codes INTEGER DEFAULT 0,
                normalized_candidate_codes INTEGER DEFAULT 0,
                mappings INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                settings_json TEXT,
                step_versions_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS output_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_signature TEXT NOT NULL,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                exists_flag INTEGER NOT NULL DEFAULT 0,
                rows_count INTEGER DEFAULT 0,
                bytes_size INTEGER DEFAULT 0,
                updated_at TEXT,
                UNIQUE(run_signature, filename),
                FOREIGN KEY(run_signature) REFERENCES runs(signature) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS run_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_signature TEXT NOT NULL,
                created_at TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY(run_signature) REFERENCES runs(signature) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            INSERT INTO app_meta(key, value)
            VALUES ('schema_version', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(SCHEMA_VERSION),),
        )
    return db_path


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def count_csv_rows(path: Path) -> int:
    if not path.exists() or path.stat().st_size == 0:
        return 0
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f)
            row_count = sum(1 for _ in reader)
        return max(0, row_count - 1)
    except Exception:
        return 0


def upsert_run(
    local_results_dir: Path,
    *,
    signature: str,
    project_dir: Path,
    status: str,
    model: str,
    run_until: str,
    preset: str,
    settings: dict[str, Any],
    step_versions: dict[str, Any],
) -> None:
    init_database(local_results_dir)
    now = utc_now_iso()
    db_path = get_database_path(local_results_dir)
    with connect(db_path) as conn:
        existing = conn.execute("SELECT created_at FROM runs WHERE signature = ?", (signature,)).fetchone()
        created_at = existing["created_at"] if existing else now
        conn.execute(
            """
            INSERT INTO runs (
                signature, project_dir, status, created_at, updated_at, model,
                run_until, preset, settings_json, step_versions_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(signature) DO UPDATE SET
                project_dir = excluded.project_dir,
                status = excluded.status,
                updated_at = excluded.updated_at,
                model = excluded.model,
                run_until = excluded.run_until,
                preset = excluded.preset,
                settings_json = excluded.settings_json,
                step_versions_json = excluded.step_versions_json
            """,
            (
                signature,
                str(project_dir),
                status,
                created_at,
                now,
                model,
                run_until,
                preset,
                _json_dumps(settings),
                _json_dumps(step_versions),
            ),
        )


def add_event(local_results_dir: Path, signature: str, message: str, *, level: str = "info") -> None:
    init_database(local_results_dir)
    with connect(get_database_path(local_results_dir)) as conn:
        conn.execute(
            "INSERT INTO run_events(run_signature, created_at, level, message) VALUES (?, ?, ?, ?)",
            (signature, utc_now_iso(), level, message),
        )


def refresh_run_outputs(local_results_dir: Path, project_dir: Path, *, status: str | None = None) -> None:
    init_database(local_results_dir)
    manifest_path = project_dir / "manifest.json"
    signature = project_dir.name
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            signature = str(manifest.get("signature") or signature)
        except Exception:
            pass

    counts = {
        "raw_rows": count_csv_rows(project_dir / "01_raw_dataset.csv"),
        "opinion_units": count_csv_rows(project_dir / "02_opinion_units.csv"),
        "raw_candidate_codes": count_csv_rows(project_dir / "04_candidate_summary.csv"),
        "normalized_candidate_codes": count_csv_rows(project_dir / "06_candidate_summary_normalized.csv"),
        "mappings": count_csv_rows(project_dir / "05_candidate_code_mapping.csv"),
        "errors": (
            count_csv_rows(project_dir / "02_errors.csv")
            + count_csv_rows(project_dir / "02c_pos_errors.csv")
            + count_csv_rows(project_dir / "03_candidate_errors.csv")
            + count_csv_rows(project_dir / "05_candidate_normalization_errors.csv")
        ),
    }

    now = utc_now_iso()
    output_mtimes = [
        (project_dir / filename).stat().st_mtime
        for filename in OUTPUT_FILES
        if (project_dir / filename).exists()
    ]
    file_updated_at = (
        datetime.fromtimestamp(max(output_mtimes)).isoformat(timespec="seconds")
        if output_mtimes
        else now
    )
    run_updated_at = now if status else file_updated_at
    with connect(get_database_path(local_results_dir)) as conn:
        existing = conn.execute("SELECT signature FROM runs WHERE signature = ?", (signature,)).fetchone()
        if not existing:
            conn.execute(
                """
                INSERT INTO runs(signature, project_dir, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (signature, str(project_dir), status or "imported", file_updated_at, run_updated_at),
            )

        update_values = [
            str(project_dir),
            run_updated_at,
            counts["raw_rows"],
            counts["opinion_units"],
            counts["raw_candidate_codes"],
            counts["normalized_candidate_codes"],
            counts["mappings"],
            counts["errors"],
            signature,
        ]
        conn.execute(
            """
            UPDATE runs
            SET project_dir = ?,
                updated_at = ?,
                raw_rows = ?,
                opinion_units = ?,
                raw_candidate_codes = ?,
                normalized_candidate_codes = ?,
                mappings = ?,
                errors = ?
            WHERE signature = ?
            """,
            update_values,
        )
        if status:
            conn.execute(
                "UPDATE runs SET status = ?, updated_at = ? WHERE signature = ?",
                (status, run_updated_at, signature),
            )

        for filename in OUTPUT_FILES:
            path = project_dir / filename
            exists_flag = 1 if path.exists() else 0
            rows_count = count_csv_rows(path) if path.suffix.lower() == ".csv" else 0
            bytes_size = path.stat().st_size if path.exists() else 0
            updated_at = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds") if path.exists() else None
            conn.execute(
                """
                INSERT INTO output_files (
                    run_signature, filename, path, exists_flag, rows_count, bytes_size, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_signature, filename) DO UPDATE SET
                    path = excluded.path,
                    exists_flag = excluded.exists_flag,
                    rows_count = excluded.rows_count,
                    bytes_size = excluded.bytes_size,
                    updated_at = excluded.updated_at
                """,
                (signature, filename, str(path), exists_flag, rows_count, bytes_size, updated_at),
            )


def list_runs(local_results_dir: Path) -> list[dict[str, Any]]:
    init_database(local_results_dir)
    with connect(get_database_path(local_results_dir)) as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM runs
            ORDER BY updated_at DESC, created_at DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_run(local_results_dir: Path, signature: str) -> dict[str, Any] | None:
    init_database(local_results_dir)
    with connect(get_database_path(local_results_dir)) as conn:
        row = conn.execute("SELECT * FROM runs WHERE signature = ?", (signature,)).fetchone()
    return dict(row) if row else None
