"""ReviewRun domain model."""

from __future__ import annotations

from dataclasses import dataclass

from sycamore.models.enums import UserDecision


@dataclass(frozen=True)
class ReviewRun:
    id: str
    node_id: str
    mental_model_hash: str
    prompt_version: str
    provider: str
    summary: str
    user_decision: UserDecision
    created_at: str
    model: str | None = None
    fact_issues_json: str | None = None
    boundary_issues_json: str | None = None
    questions_json: str | None = None
    practice_suggestions_json: str | None = None
    raw_output_path: str | None = None
