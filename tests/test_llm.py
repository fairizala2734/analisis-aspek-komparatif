from llm.cache import call_hash
from llm.client import LLMClient, LLMUsage
from llm.mock import MockLLM
from llm.prompts.registry import prompt_hashes


def test_call_hash_is_deterministic() -> None:
    first = call_hash("prompt", {"answer": "contoh"}, "model")
    second = call_hash("prompt", {"answer": "contoh"}, "model")
    assert first == second


def test_mock_llm_is_deterministic() -> None:
    client = MockLLM()
    payload = {"answer": "A lebih awet daripada B."}
    assert client.call_json("prompt", payload) == client.call_json("prompt", payload)


def test_all_prompts_have_hashes() -> None:
    hashes = prompt_hashes()
    assert set(hashes) == {
        "opinion_units",
        "candidate_codes",
        "candidate_normalization",
        "comparative_validation",
        "overmerge_relabel",
    }
    assert all(len(value) == 64 for value in hashes.values())


def test_llm_cache_can_be_bypassed_and_refreshed(tmp_path, monkeypatch) -> None:
    payload = {"row_id": 1, "question": "A dibanding B?"}
    client = LLMClient(
        base_url="https://example.invalid/api/v1",
        api_key="test-key",
        model="test-model",
        cache_dir=tmp_path,
        read_cache=False,
    )
    key = call_hash("prompt", payload, "test-model")
    client.cache.put(key, {"source": "old-cache"})
    calls = []

    def fake_request(system_prompt, user_payload):
        calls.append((system_prompt, user_payload))
        return '{"source":"fresh"}', LLMUsage()

    monkeypatch.setattr(client, "_request", fake_request)
    result = client.call_json(
        "prompt",
        payload,
        retry_per_call=0,
        always_retry=False,
    )

    assert result == {"source": "fresh"}
    assert len(calls) == 1
    assert client.cache.get(key) == {"source": "fresh"}
