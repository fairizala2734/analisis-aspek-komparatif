"""CSV contract validation between scientific pipeline steps."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from pipeline.schemas import (
    CANDIDATE_COLUMNS,
    NORMALIZATION_MAPPING_COLUMNS,
    NORMALIZED_COLUMNS,
    NORMALIZED_SUMMARY_COLUMNS,
    OUTPUT_COLUMNS,
    POS_COLUMNS,
    SUMMARY_COLUMNS,
)


@dataclass(frozen=True)
class CSVContract:
    filename: str
    columns: tuple[str, ...]

    def validate(self, frame: pd.DataFrame, *, exact_order: bool = True) -> None:
        actual = list(frame.columns)
        expected = list(self.columns)
        missing = [column for column in expected if column not in actual]
        if missing:
            raise ValueError(f"{self.filename}: kolom wajib hilang: {missing}")
        if exact_order and actual[: len(expected)] != expected:
            raise ValueError(
                f"{self.filename}: urutan kolom tidak kompatibel. "
                f"Expected prefix={expected}, actual={actual}"
            )


CONTRACTS = {
    "02_opinion_units.csv": CSVContract("02_opinion_units.csv", tuple(OUTPUT_COLUMNS)),
    "02c_opinion_units_pos.csv": CSVContract(
        "02c_opinion_units_pos.csv",
        tuple(POS_COLUMNS),
    ),
    "03_candidate_codes.csv": CSVContract("03_candidate_codes.csv", tuple(CANDIDATE_COLUMNS)),
    "04_candidate_summary.csv": CSVContract("04_candidate_summary.csv", tuple(SUMMARY_COLUMNS)),
    "05_candidate_code_mapping.csv": CSVContract(
        "05_candidate_code_mapping.csv",
        tuple(NORMALIZATION_MAPPING_COLUMNS),
    ),
    "05_candidate_code_normalized.csv": CSVContract(
        "05_candidate_code_normalized.csv",
        tuple(NORMALIZED_COLUMNS),
    ),
    "06_candidate_summary_normalized.csv": CSVContract(
        "06_candidate_summary_normalized.csv",
        tuple(NORMALIZED_SUMMARY_COLUMNS),
    ),
}


def validate_frame(filename: str, frame: pd.DataFrame, *, exact_order: bool = True) -> None:
    contract = CONTRACTS.get(filename)
    if contract:
        contract.validate(frame, exact_order=exact_order)


def validate_csv(path: Path, *, exact_order: bool = True) -> None:
    if path.name not in CONTRACTS or not path.exists():
        return
    validate_frame(path.name, pd.read_csv(path, encoding="utf-8-sig"), exact_order=exact_order)


def reindex_contract(frame: pd.DataFrame, columns: Sequence[str]) -> pd.DataFrame:
    return frame.reindex(columns=list(columns))
