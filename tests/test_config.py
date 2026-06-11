from pipeline.config import load_settings


def test_streamlit_secrets_overlay_uses_field_names() -> None:
    settings = load_settings(
        {
            "llm": {
                "api_key": "test-key",
                "model": "test/model",
                "max_tokens": 4321,
            },
            "app": {"local_results_dir": "test-results"},
        }
    )

    assert settings.llm_api_key == "test-key"
    assert settings.llm_model == "test/model"
    assert settings.llm_max_tokens == 4321
    assert str(settings.local_results_dir) == "test-results"
