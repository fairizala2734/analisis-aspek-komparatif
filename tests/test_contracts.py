import pandas as pd
import pytest

from pipeline.contracts import validate_frame
from pipeline.schemas import CANDIDATE_COLUMNS


def test_candidate_contract_accepts_stable_columns() -> None:
    validate_frame("03_candidate_codes.csv", pd.DataFrame(columns=CANDIDATE_COLUMNS))


def test_candidate_contract_rejects_missing_column() -> None:
    with pytest.raises(ValueError, match="kolom wajib hilang"):
        validate_frame("03_candidate_codes.csv", pd.DataFrame(columns=CANDIDATE_COLUMNS[:-1]))
