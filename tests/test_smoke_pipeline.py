from pathlib import Path

import pandas as pd

from llm.mock import MockLLM
from pipeline.ingest.csv_io import save_df
from pipeline.schemas import (
    CANDIDATE_COLUMNS,
    NORMALIZATION_MAPPING_COLUMNS,
    NORMALIZED_COLUMNS,
    NORMALIZED_SUMMARY_COLUMNS,
    OUTPUT_COLUMNS,
    POS_COLUMNS,
    SUMMARY_COLUMNS,
)


def _row(columns: list[str], **values: object) -> pd.DataFrame:
    row = {column: "" for column in columns}
    row.update(values)
    return pd.DataFrame([row], columns=columns)


def test_smoke_01_to_06_with_mock_llm(tmp_path: Path) -> None:
    mock = MockLLM()
    raw = pd.DataFrame(
        [{"row_id": 1, "question": "Mana lebih awet?", "answer": "A lebih awet daripada B."}]
    )
    save_df(raw, tmp_path / "01_raw_dataset.csv")

    opinion_response = mock.call_json("opinion", {"answer": raw.iloc[0]["answer"]})
    opinion = _row(
        OUTPUT_COLUMNS,
        global_opinion_id="1_1",
        row_id=1,
        question=raw.iloc[0]["question"],
        answer=raw.iloc[0]["answer"],
        opinion_id=1,
        opinion_unit=opinion_response["items"][0]["opinion_unit"],
    )
    save_df(opinion, tmp_path / "02_opinion_units.csv")

    pos = _row(POS_COLUMNS, **opinion.iloc[0].to_dict())
    save_df(pos, tmp_path / "02c_opinion_units_pos.csv")

    candidate_response = mock.call_json(
        "candidate",
        {"opinion_unit": opinion.iloc[0]["opinion_unit"], "main_opinion": "lebih awet"},
    )
    candidate = _row(
        CANDIDATE_COLUMNS,
        **{key: value for key, value in pos.iloc[0].to_dict().items() if key in CANDIDATE_COLUMNS},
        candidate_code=candidate_response["candidate_code"],
        candidate_reason=candidate_response["candidate_reason"],
        candidate_confidence=candidate_response["confidence"],
    )
    save_df(candidate, tmp_path / "03_candidate_codes.csv")

    summary = _row(SUMMARY_COLUMNS, candidate_code="aspek", frequency=1)
    save_df(summary, tmp_path / "04_candidate_summary.csv")

    normalization_response = mock.call_json(
        "normalization",
        {"items": [{"candidate_code": "aspek"}], "total_unique_candidate_codes": 1},
    )
    assert normalization_response["reviewed_count"] == 1
    mapping = _row(
        NORMALIZATION_MAPPING_COLUMNS,
        original_candidate_code="aspek",
        normalized_candidate_code="aspek",
        normalization_action="keep",
        frequency=1,
    )
    save_df(mapping, tmp_path / "05_candidate_code_mapping.csv")
    normalized = _row(
        NORMALIZED_COLUMNS,
        **candidate.iloc[0].to_dict(),
        original_candidate_code="aspek",
        normalized_candidate_code="aspek",
        normalization_action="keep",
    )
    save_df(normalized, tmp_path / "05_candidate_code_normalized.csv")

    final_summary = _row(
        NORMALIZED_SUMMARY_COLUMNS,
        normalized_candidate_code="aspek",
        frequency=1,
        original_candidate_codes="aspek",
    )
    save_df(final_summary, tmp_path / "06_candidate_summary_normalized.csv")

    assert len(mock.calls) == 3
    assert (tmp_path / "06_candidate_summary_normalized.csv").exists()
