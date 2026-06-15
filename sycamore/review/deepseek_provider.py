"""DeepSeek OpenAI-compatible review provider."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from sycamore.review.prompt import (
    SYSTEM_CRITIQUE_PROMPT,
    ReviewPayload,
    build_critique_user_prompt,
)
from sycamore.review.provider import ReviewCritique

_JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class DeepSeekReviewProvider:
    name = "deepseek"

    def __init__(
        self,
        *,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-v4-pro",
        api_key_env: str = "DEEPSEEK_API_KEY",
        timeout_seconds: int = 120,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key_env = api_key_env
        self._timeout_seconds = timeout_seconds

    def _chat_completions_url(self) -> str:
        if self._base_url.endswith("/chat/completions"):
            return self._base_url
        if self._base_url.endswith("/v1"):
            return f"{self._base_url}/chat/completions"
        return f"{self._base_url}/chat/completions"

    def _api_key(self) -> str:
        api_key = os.environ.get(self._api_key_env, "").strip()
        if not api_key:
            raise RuntimeError(
                f"Missing API key in environment variable {self._api_key_env}. "
                "Copy .env.example to .env and set DEEPSEEK_API_KEY."
            )
        return api_key

    @staticmethod
    def _parse_json_content(content: str) -> dict[str, object]:
        text = content.strip()
        fenced = _JSON_BLOCK_PATTERN.search(text)
        if fenced:
            text = fenced.group(1).strip()
        parsed = json.loads(text)
        if not isinstance(parsed, dict):
            raise ValueError("DeepSeek response JSON must be an object.")
        return parsed

    def critique(self, payload: ReviewPayload) -> ReviewCritique:
        request_body = json.dumps(
            {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": SYSTEM_CRITIQUE_PROMPT},
                    {"role": "user", "content": build_critique_user_prompt(payload)},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            self._chat_completions_url(),
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key()}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"DeepSeek API HTTP {error.code}: {body}") from error
        except urllib.error.URLError as error:
            raise RuntimeError(f"DeepSeek API request failed: {error}") from error
        except json.JSONDecodeError as error:
            raise RuntimeError("DeepSeek API returned invalid JSON.") from error

        try:
            message = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as error:
            raise RuntimeError("DeepSeek API response missing choices[0].message.content.") from error

        parsed = self._parse_json_content(str(message))
        return ReviewCritique(
            summary=str(parsed.get("summary", "")),
            fact_issues=[str(item) for item in parsed.get("factIssues", [])],
            boundary_issues=[str(item) for item in parsed.get("boundaryIssues", [])],
            questions=[str(item) for item in parsed.get("questions", [])],
            practice_suggestions=[str(item) for item in parsed.get("practiceSuggestions", [])],
            model=str(raw.get("model", self._model)),
        )

    def suggest_fill(self, prompt: str) -> str:
        """Generate a short fill suggestion for an edit block."""
        request_body = json.dumps(
            {
                "model": self._model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are helping a learner fill in a knowledge node. "
                            "Respond with a single, concise, actionable suggestion "
                            "in the user's language. Do NOT write a full paragraph — "
                            "just 1-3 sentences that the user can edit and expand."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            self._chat_completions_url(),
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key()}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except Exception as error:
            # Silently fall back — network issues shouldn't block editing
            return f"[LLM unavailable: {error}]"

        try:
            return str(raw["choices"][0]["message"]["content"]).strip()
        except Exception:
            return "[LLM returned unexpected response]"
