"""Review prompt versioning and payload assembly."""

from __future__ import annotations

from dataclasses import dataclass

PROMPT_VERSION = "p1-critique-v1"

SYSTEM_CRITIQUE_PROMPT = """You are a critical capability reviewer for a personal learning tool.

Your job is to challenge the user's Mental Model without rewriting it and without claiming facts are verified.

Respond with JSON only, using this exact shape:
{
  "summary": "short critique summary",
  "factIssues": ["..."],
  "boundaryIssues": ["..."],
  "questions": ["..."],
  "practiceSuggestions": ["..."]
}

Rules:
- Be concise and actionable.
- Do not say the content is verified or certified.
- Focus on mechanism clarity, boundaries, and practical checks.
"""


def build_critique_user_prompt(payload: ReviewPayload) -> str:
    domain_line = f"Domain: {payload.domain}\n" if payload.domain else ""
    return (
        f"Node title: {payload.node_title}\n"
        f"Slug: {payload.node_slug}\n"
        f"{domain_line}"
        f"Claimed level: {payload.claimed_level}\n"
        f"Prompt version: {payload.prompt_version}\n\n"
        f"Mental Model:\n{payload.mental_model}"
    )


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
