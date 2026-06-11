"""Storage facade preserving the former ``storage.py`` API."""

from storage.database import (
    add_event,
    connect,
    count_csv_rows,
    get_database_path,
    get_run,
    init_database,
    list_runs,
    refresh_run_outputs,
    upsert_run,
)

__all__ = [
    "add_event",
    "connect",
    "count_csv_rows",
    "get_database_path",
    "get_run",
    "init_database",
    "list_runs",
    "refresh_run_outputs",
    "upsert_run",
]
