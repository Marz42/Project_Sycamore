import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from sycamore.review.deepseek_provider import DeepSeekReviewProvider
from sycamore.review.factory import get_review_provider
from sycamore.review.prompt import build_review_payload
from sycamore.review.provider import MockReviewProvider
from sycamore.utils.env import load_dotenv_file


def _sample_payload():
    return build_review_payload(
        node_id="node-1",
        node_title="我能用 awk 处理日志",
        node_slug="awk-logs",
        domain="shell",
        claimed_level="L1",
        mental_model="awk 适合按列处理结构化文本。",
        mental_model_hash="abc123",
    )


def test_factory_returns_mock_when_llm_disabled() -> None:
    provider = get_review_provider({"llm": {"enabled": False, "provider": "deepseek"}})
    assert isinstance(provider, MockReviewProvider)


def test_factory_returns_deepseek_when_enabled() -> None:
    provider = get_review_provider(
        {
            "llm": {
                "enabled": True,
                "provider": "deepseek",
                "base_url": "https://api.deepseek.com",
                "model": "deepseek-v4-pro",
                "api_key_env": "DEEPSEEK_API_KEY",
            }
        }
    )
    assert provider.name == "deepseek"
    assert isinstance(provider, DeepSeekReviewProvider)


def test_deepseek_provider_parses_chat_completion_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    provider = DeepSeekReviewProvider()
    payload = _sample_payload()
    api_response = {
        "model": "deepseek-v4-pro",
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "summary": "Needs tighter mechanism wording.",
                            "factIssues": ["Check field separator behavior."],
                            "boundaryIssues": ["Not ideal for binary logs."],
                            "questions": ["What happens with multi-byte separators?"],
                            "practiceSuggestions": ["Parse one real log file."],
                        }
                    )
                }
            }
        ],
    }

    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.read.return_value = json.dumps(
            api_response
        ).encode("utf-8")
        critique = provider.critique(payload)

    assert critique.summary.startswith("Needs tighter")
    assert critique.model == "deepseek-v4-pro"
    assert "field separator" in critique.fact_issues[0]


def test_deepseek_provider_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    provider = DeepSeekReviewProvider()

    with pytest.raises(RuntimeError, match="DEEPSEEK_API_KEY"):
        provider.critique(_sample_payload())


def test_load_dotenv_file_sets_missing_variables(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEEPSEEK_API_KEY=from-dotenv\nSYCA_LLM_MODEL=deepseek-v4-pro\n",
        encoding="utf-8",
    )
    original = os.environ.pop("DEEPSEEK_API_KEY", None)
    try:
        load_dotenv_file(env_file)
        assert os.environ["DEEPSEEK_API_KEY"] == "from-dotenv"
    finally:
        if original is None:
            os.environ.pop("DEEPSEEK_API_KEY", None)
        else:
            os.environ["DEEPSEEK_API_KEY"] = original
