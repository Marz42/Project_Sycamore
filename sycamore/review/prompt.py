"""Review prompt versioning and payload assembly."""

from __future__ import annotations

from dataclasses import dataclass

PROMPT_VERSION = "p1-critique-v1"


@dataclass(frozen=True)
class ReviewPayload:
    node_id: str
    node_title: str
    node_slug: str
    domain: str | None
    claimed_level: str
    mental_model: str
    mental_model_hash: str
    prompt_version: str


def build_review_payload(
    *,
    node_id: str,
    node_title: str,
    node_slug: str,
    domain: str | None,
    claimed_level: str,
    mental_model: str,
    mental_model_hash: str,
) -> ReviewPayload:
    return ReviewPayload(
        node_id=node_id,
        node_title=node_title,
        node_slug=node_slug,
        domain=domain,
        claimed_level=claimed_level,
        mental_model=mental_model,
        mental_model_hash=mental_model_hash,
        prompt_version=PROMPT_VERSION,
    )
