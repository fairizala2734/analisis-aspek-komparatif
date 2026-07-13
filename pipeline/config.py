"""Application configuration with environment-first settings."""

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # pragma: no cover - compatibility until dependencies are installed
    BaseSettings = BaseModel  # type: ignore[misc,assignment]
    SettingsConfigDict = dict  # type: ignore[misc,assignment]


APP_VERSION = "2.0.0"


class AppSettings(BaseSettings):
    """Runtime settings shared by Streamlit, the pipeline, and tests."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias="LLM_BASE_URL",
    )
    llm_api_key: str = Field(default="", validation_alias="OPENROUTER_API_KEY")
    llm_model: str = Field(
        default="openai/gpt-oss-120b:free",
        validation_alias="OPENROUTER_MODEL",
    )
    llm_temperature: float = Field(default=0.0, validation_alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=4000, validation_alias="LLM_MAX_TOKENS")
    llm_use_json_mode: bool = Field(default=False, validation_alias="LLM_USE_JSON_MODE")
    llm_retry_base_sleep: float = Field(default=4.0, validation_alias="LLM_RETRY_BASE_SLEEP")
    llm_retry_max_sleep: float = Field(default=30.0, validation_alias="LLM_RETRY_MAX_SLEEP")
    llm_always_retry: bool = Field(default=True, validation_alias="LLM_ALWAYS_RETRY_PER_CALL")
    openrouter_http_referer: str = Field(
        default="http://localhost:8501",
        validation_alias="OPENROUTER_HTTP_REFERER",
    )
    openrouter_app_title: str = Field(
        default="Opinion Unit Extractor",
        validation_alias="OPENROUTER_APP_TITLE",
    )
    local_results_dir: Path = Field(default=Path("local_results"), validation_alias="LOCAL_RESULTS_DIR")


def _secret(secrets: Mapping[str, Any], section: str, key: str, default: Any) -> Any:
    value = secrets.get(section, {})
    if isinstance(value, Mapping):
        return value.get(key, default)
    return default


def load_settings(secrets: Mapping[str, Any] | None = None) -> AppSettings:
    """Load environment settings and optionally overlay Streamlit secrets."""

    env_values: dict[str, Any] = {}
    env_map = {
        "llm_base_url": "LLM_BASE_URL",
        "llm_api_key": "OPENROUTER_API_KEY",
        "llm_model": "OPENROUTER_MODEL",
        "llm_temperature": "LLM_TEMPERATURE",
        "llm_max_tokens": "LLM_MAX_TOKENS",
        "llm_use_json_mode": "LLM_USE_JSON_MODE",
        "llm_retry_base_sleep": "LLM_RETRY_BASE_SLEEP",
        "llm_retry_max_sleep": "LLM_RETRY_MAX_SLEEP",
        "llm_always_retry": "LLM_ALWAYS_RETRY_PER_CALL",
        "openrouter_http_referer": "OPENROUTER_HTTP_REFERER",
        "openrouter_app_title": "OPENROUTER_APP_TITLE",
        "local_results_dir": "LOCAL_RESULTS_DIR",
    }
    for field, env_name in env_map.items():
        if env_name in os.environ:
            env_values[field] = os.environ[env_name]
    settings = AppSettings.model_validate(env_values)
    if not secrets:
        return settings

    values = settings.model_dump()
    values.update(
        {
            "llm_base_url": _secret(secrets, "llm", "base_url", settings.llm_base_url),
            "llm_api_key": _secret(secrets, "llm", "api_key", settings.llm_api_key),
            "llm_model": _secret(secrets, "llm", "model", settings.llm_model),
            "llm_temperature": _secret(secrets, "llm", "temperature", settings.llm_temperature),
            "llm_max_tokens": _secret(secrets, "llm", "max_tokens", settings.llm_max_tokens),
            "llm_use_json_mode": _secret(secrets, "llm", "use_json_mode", settings.llm_use_json_mode),
            "llm_retry_base_sleep": _secret(
                secrets,
                "llm",
                "retry_base_sleep",
                settings.llm_retry_base_sleep,
            ),
            "llm_retry_max_sleep": _secret(
                secrets,
                "llm",
                "retry_max_sleep",
                settings.llm_retry_max_sleep,
            ),
            "llm_always_retry": _secret(
                secrets,
                "llm",
                "always_retry_per_call",
                settings.llm_always_retry,
            ),
            "openrouter_http_referer": _secret(
                secrets,
                "openrouter",
                "http_referer",
                settings.openrouter_http_referer,
            ),
            "openrouter_app_title": _secret(
                secrets,
                "openrouter",
                "app_title",
                settings.openrouter_app_title,
            ),
            "local_results_dir": Path(
                _secret(secrets, "app", "local_results_dir", settings.local_results_dir)
            ),
        }
    )
    return AppSettings.model_validate(values)


STEP_VERSIONS = {
    "raw_dataset": "v1",
    "opinion_units": "v12_user_defined_entity_context",
    "pos_tagging": "v1_stanza_main_counterpart_pos",
    "candidate_codes": "v1_pos_guided_single_opinion_unit",
    "candidate_normalization": "v4_group_first_compact_global_mapping",
    "candidate_summary": "v2_python_groupby_normalized_candidate_code",
    "aspect_network": "v1_dataset_adaptive_aspect_network",
}


RUN_UNTIL_OPTIONS = {
    "Sampai raw dataset saja (01)": "raw_dataset",
    "Sampai opinion_units (02)": "opinion_units",
    "Sampai POS tagging Stanza (02c)": "pos_tagging",
    "Sampai candidate_codes (03)": "candidate_codes",
    "Sampai normalisasi candidate_code (05)": "candidate_normalization",
    "Sampai candidate_summary normalisasi (06)": "candidate_summary",
    "Sampai jaringan aspek (07)": "aspect_network",
}
