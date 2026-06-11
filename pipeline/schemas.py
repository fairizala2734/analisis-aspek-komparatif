"""Stable CSV contracts and runtime schemas."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

OUTPUT_COLUMNS = [
    "global_opinion_id",
    "row_id",
    "question",
    "answer",
    "answer_python_cleaned",
    "answer_cleaned",
    "opinion_id",
    "opinion_unit",
    "main_entity",
    "main_opinion",
    "main_sentiment",
    "main_source",
    "main_evidence_text",
    "counterpart_entity",
    "counterpart_opinion",
    "counterpart_sentiment",
    "counterpart_source",
    "counterpart_evidence_text",
    "counterpart_logic",
    "confidence",
]

ERROR_COLUMNS = [
    "row_id",
    "question",
    "answer",
    "answer_python_cleaned",
    "step",
    "error_type",
    "error_message",
    "traceback",
]

POS_COLUMNS = OUTPUT_COLUMNS + [
    "main_pos_tokens",
    "counterpart_pos_tokens",
    "main_noun_candidates",
    "counterpart_noun_candidates",
]

CANDIDATE_COLUMNS = [
    "global_opinion_id",
    "row_id",
    "question",
    "answer",
    "opinion_id",
    "opinion_unit",
    "main_entity",
    "main_opinion",
    "main_sentiment",
    "counterpart_entity",
    "counterpart_opinion",
    "counterpart_sentiment",
    "main_pos_tokens",
    "counterpart_pos_tokens",
    "main_noun_candidates",
    "counterpart_noun_candidates",
    "candidate_code",
    "main_position",
    "counterpart_position",
    "candidate_reason",
    "candidate_confidence",
]

CANDIDATE_ERROR_COLUMNS = [
    "global_opinion_id",
    "row_id",
    "opinion_unit",
    "step",
    "error_type",
    "error_message",
    "traceback",
]

SUMMARY_COLUMNS = [
    "candidate_code",
    "frequency",
    "supporting_opinion_ids",
    "sample_opinion_units",
    "main_entities",
    "counterpart_entities",
    "sentiments",
    "main_positions",
    "counterpart_positions",
    "candidate_reasons",
]

NORMALIZED_COLUMNS = CANDIDATE_COLUMNS + [
    "original_candidate_code",
    "normalized_candidate_code",
    "normalization_action",
    "normalization_reason",
    "normalization_confidence",
]

NORMALIZATION_MAPPING_COLUMNS = [
    "original_candidate_code",
    "normalized_candidate_code",
    "normalization_action",
    "normalization_reason",
    "normalization_confidence",
    "frequency",
    "sample_opinion_units",
]

NORMALIZED_SUMMARY_COLUMNS = [
    "normalized_candidate_code",
    "frequency",
    "original_candidate_codes",
    "supporting_opinion_ids",
    "sample_opinion_units",
    "main_entities",
    "counterpart_entities",
    "sentiments",
    "main_positions",
    "counterpart_positions",
    "candidate_reasons",
    "normalization_reasons",
]


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    IMPORTED = "imported"


class StepStatus(str, Enum):
    PENDING = "pending"
    CACHED = "cached"
    RUNNING = "running"
    OK = "ok"
    ERROR = "error"
    SKIPPED = "skipped"


class RunSettings(BaseModel):
    model_id: str
    comparison_entities: list[dict[str, Any]] = Field(default_factory=list)
    force_all_comparative: bool = False
    run_until: str = "candidate_summary"
    force_from_start: bool = False
    force_from_step_enabled: bool = False
    force_from_step: str = ""
    retry_only_error: bool = True
    max_rows: int = 0
    stanza_lang: str = "id"
    auto_download_stanza: bool = True
    use_raw_dataset_cache: bool = True
    always_retry: bool = True
    retry_per_call: int = 0
    timeout_seconds: int = 180
    save_raw_responses: bool = False
    preset: str = "Analisis penuh"


class ManifestRecord(BaseModel):
    signature: str
    run_id: str
    app_version: str
    created_or_updated_at: str
    model: str
    base_url: str
    step_versions: dict[str, str]
    prompt_hashes: dict[str, str]
    settings: dict[str, Any]
    params: dict[str, Any] = Field(default_factory=dict)
