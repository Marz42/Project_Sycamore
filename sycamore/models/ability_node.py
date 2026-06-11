"""AbilityNode domain model."""

from __future__ import annotations

from dataclasses import dataclass

from sycamore.models.enums import ClaimedLevel, ReviewStatus


@dataclass(frozen=True)
class AbilityNode:
    id: str
    slug: str
    title: str
    domain: str | None
    claimed_level: ClaimedLevel
    review_status: ReviewStatus
    node_path: str
    content_hash: str
    front_matter_hash: str
    created_at: str
    updated_at: str
    last_synced_at: str | None = None
