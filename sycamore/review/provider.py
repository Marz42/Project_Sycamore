"""LLM Provider adapters for critique reviews."""

from __future__ import annotations

import json
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


def critique_to_raw_json(critique: ReviewCritique, payload: ReviewPayload) -> dict[str, object]:
    return {
        "provider": MockReviewProvider.name,
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


def dumps_critique_raw(critique: ReviewCritique, payload: ReviewPayload) -> str:
    return json.dumps(critique_to_raw_json(critique, payload), ensure_ascii=False, indent=2)
