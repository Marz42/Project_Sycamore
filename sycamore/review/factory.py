"""Construct ReviewProvider instances from config."""

from __future__ import annotations

from typing import Any

from sycamore.review.deepseek_provider import DeepSeekReviewProvider
from sycamore.review.provider import HttpReviewProvider, MockReviewProvider, ReviewProvider

DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"
DEFAULT_DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"


def get_review_provider(config: dict[str, Any]) -> ReviewProvider:
    llm = config.get("llm", {})
    if not isinstance(llm, dict):
        return MockReviewProvider()

    provider_name = str(llm.get("provider", "deepseek") or "deepseek")
    if not llm.get("enabled", False):
        return MockReviewProvider()

    if provider_name == "deepseek":
        return DeepSeekReviewProvider(
            base_url=str(llm.get("base_url", DEFAULT_DEEPSEEK_BASE_URL) or DEFAULT_DEEPSEEK_BASE_URL),
            model=str(llm.get("model", DEFAULT_DEEPSEEK_MODEL) or DEFAULT_DEEPSEEK_MODEL),
            api_key_env=str(llm.get("api_key_env", DEFAULT_DEEPSEEK_API_KEY_ENV) or DEFAULT_DEEPSEEK_API_KEY_ENV),
        )

    if provider_name == "http":
        endpoint = str(llm.get("endpoint", "") or "")
        if not endpoint:
            raise ValueError("LLM provider 'http' requires [llm] endpoint in config.toml.")
        return HttpReviewProvider(
            endpoint=endpoint,
            model=str(llm.get("model", "") or ""),
            api_key_env=str(llm.get("api_key_env", "") or ""),
        )

    if provider_name == "mock":
        return MockReviewProvider()

    raise ValueError(f"Unsupported LLM provider: {provider_name}")
