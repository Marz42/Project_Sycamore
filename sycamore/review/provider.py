"""LLM Provider adapters for critique reviews."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from sycamore.review.prompt import ReviewPayload


@dataclass(frozen=True)
class ReviewCritique:
    summary: str
    fact_issues: list[str]
    boundary_issues: list[str]
    questions: list[str]
    practice_suggestions: list[str]
    model: str


class ReviewProvider(Protocol):
    name: str

    def critique(self, payload: ReviewPayload) -> ReviewCritique: ...


class MockReviewProvider:
    name = "mock"

    def critique(self, payload: ReviewPayload) -> ReviewCritique:
        preview = payload.mental_model.strip().splitlines()[0] if payload.mental_model.strip() else ""
        return ReviewCritique(
            summary=(
                f"Mock critique for '{payload.node_title}'. "
                "This review challenges understanding; it does not verify facts."
            ),
            fact_issues=[
                "Confirm whether the core mechanism is stated precisely enough to act on."
            ],
            boundary_issues=[
                "Clarify where this capability stops being the right tool."
            ],
            questions=[
                f"What would break if you applied this outside its intended scenario? ({preview})"
            ],
            practice_suggestions=[
                "Run one small real task and log the outcome in Practice Log."
            ],
            model="mock-critique-v1",
        )


class HttpReviewProvider:
    name = "http"

    def __init__(self, *, endpoint: str, model: str = "", api_key_env: str = "") -> None:
        self._endpoint = endpoint
        self._model = model
        self._api_key_env = api_key_env

    def critique(self, payload: ReviewPayload) -> ReviewCritique:
        request_body = json.dumps(
            {
                "promptVersion": payload.prompt_version,
                "nodeId": payload.node_id,
                "nodeTitle": payload.node_title,
                "nodeSlug": payload.node_slug,
                "domain": payload.domain,
                "claimedLevel": payload.claimed_level,
                "mentalModel": payload.mental_model,
                "mentalModelHash": payload.mental_model_hash,
                "model": self._model or None,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key_env:
            api_key = os.environ.get(self._api_key_env)
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"

        request = urllib.request.Request(
            self._endpoint,
            data=request_body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as error:
            raise RuntimeError(f"HTTP review provider failed: {error}") from error

        return ReviewCritique(
            summary=str(raw.get("summary", "")),
            fact_issues=[str(item) for item in raw.get("factIssues", [])],
            boundary_issues=[str(item) for item in raw.get("boundaryIssues", [])],
            questions=[str(item) for item in raw.get("questions", [])],
            practice_suggestions=[str(item) for item in raw.get("practiceSuggestions", [])],
            model=str(raw.get("model", self._model or "http-provider")),
        )


def critique_to_raw_json(
    critique: ReviewCritique,
    payload: ReviewPayload,
    *,
    provider_name: str,
) -> dict[str, object]:
    return {
        "provider": provider_name,
        "model": critique.model,
        "promptVersion": payload.prompt_version,
        "nodeId": payload.node_id,
        "mentalModelHash": payload.mental_model_hash,
        "summary": critique.summary,
        "factIssues": critique.fact_issues,
        "boundaryIssues": critique.boundary_issues,
        "questions": critique.questions,
        "practiceSuggestions": critique.practice_suggestions,
    }


def dumps_critique_raw(
    critique: ReviewCritique,
    payload: ReviewPayload,
    *,
    provider_name: str,
) -> str:
    return json.dumps(
        critique_to_raw_json(critique, payload, provider_name=provider_name),
        ensure_ascii=False,
        indent=2,
    )

