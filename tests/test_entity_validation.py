from io import BytesIO

import pandas as pd
import pytest

from pipeline.ingest.entity_validation import (
    canonicalize_entity,
    match_entities,
    parse_comparison_entities,
    validate_comparative_rows,
    validate_entity_setup,
)
from pipeline.ingest.raw_dataset import build_raw_dataset, normalize_raw_dataset


def _entities():
    return parse_comparison_entities(
        pd.DataFrame(
            [
                {
                    "Hal yang dibandingkan": "batik tulis",
                    "Nama lain (opsional)": "tulis, handmade",
                },
                {
                    "Hal yang dibandingkan": "batik cap",
                    "Nama lain (opsional)": "cap",
                },
            ]
        )
    )


def _stub_judger(row_id: int, question: str, matched_entities: list[str]):
    return row_id == 1, "stub"


def test_entity_setup_requires_at_least_two_items() -> None:
    with pytest.raises(ValueError, match="minimal dua"):
        validate_entity_setup(_entities()[:1])


def test_entity_matching_uses_aliases_and_word_boundaries() -> None:
    entities = _entities()
    assert match_entities("Apa perbedaan tulis dan cap?", entities) == [
        "batik tulis",
        "batik cap",
    ]
    assert match_entities("Bagaimana pencap dibanding tulis?", entities) == [
        "batik tulis"
    ]


def test_alias_is_canonicalized_to_user_name() -> None:
    assert canonicalize_entity("handmade", _entities()) == "batik tulis"


def test_rows_require_two_entities_and_comparative_question() -> None:
    source = pd.DataFrame(
        [
            {
                "pertanyaan": "Apa perbedaan batik tulis dan batik cap?",
                "jawaban": "Batik tulis lebih unik.",
            },
            {
                "pertanyaan": "Jelaskan batik tulis dan batik cap.",
                "jawaban": "Keduanya adalah batik.",
            },
            {
                "pertanyaan": "Apa kelebihan batik tulis?",
                "jawaban": "Lebih unik.",
            },
        ]
    )
    raw = normalize_raw_dataset(source, "pertanyaan", "jawaban")
    valid, report = validate_comparative_rows(raw, _entities(), comparative_judger=_stub_judger)

    assert valid["row_id"].tolist() == [1]
    assert report["validation_status"].tolist() == [
        "accepted",
        "rejected",
        "rejected",
    ]


def test_dibandingkan_is_treated_as_comparative() -> None:
    source = pd.DataFrame(
        [
            {
                "question": "Menurut Anda, apa keunggulan utama batik tulis dibandingkan batik cap?",
                "answer": "Batik tulis lebih unik.",
            }
        ]
    )
    raw = normalize_raw_dataset(source, "question", "answer")
    valid, report = validate_comparative_rows(raw, _entities(), comparative_judger=_stub_judger)

    assert valid["row_id"].tolist() == [1]
    assert report.loc[0, "comparative_status"] == "comparative"


def test_assume_comparative_only_bypasses_question_shape_check() -> None:
    source = pd.DataFrame(
        [
            {
                "question": "Jelaskan batik tulis dan batik cap.",
                "answer": "Keduanya adalah batik.",
            },
            {
                "question": "Jelaskan batik tulis.",
                "answer": "Batik.",
            },
        ]
    )
    raw = normalize_raw_dataset(source, "question", "answer")
    valid, _ = validate_comparative_rows(raw, _entities(), assume_comparative=True)

    assert valid["row_id"].tolist() == [1]


def test_build_raw_dataset_saves_only_accepted_rows(tmp_path) -> None:
    csv_bytes = (
        b"question,answer\n"
        b'"Apa perbedaan batik tulis dan batik cap?","Batik tulis lebih unik."\n'
        b'"Apa kelebihan batik tulis?","Lebih unik."\n'
    )

    result = build_raw_dataset(
        BytesIO(csv_bytes),
        max_rows=0,
        project_dir=tmp_path,
        force=True,
        q_col="question",
        a_col="answer",
        comparison_entities=_entities(),
        comparative_judger=_stub_judger,
    )

    report = pd.read_csv(tmp_path / "01_entity_validation.csv", encoding="utf-8-sig")
    assert result["row_id"].tolist() == [1]
    assert report["validation_status"].tolist() == ["accepted", "rejected"]


def test_validation_logs_entity_and_llm_checks() -> None:
    source = pd.DataFrame(
        [
            {
                "question": "Apa perbedaan batik tulis dan batik cap?",
                "answer": "Batik tulis lebih unik.",
            }
        ]
    )
    raw = normalize_raw_dataset(source, "question", "answer")
    logs = []

    validate_comparative_rows(
        raw,
        _entities(),
        comparative_judger=_stub_judger,
        log_fn=logs.append,
    )

    assert any("pemeriksaan entity" in message for message in logs)
