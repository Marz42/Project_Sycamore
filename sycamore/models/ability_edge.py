"""AbilityEdge domain model."""

from __future__ import annotations

from dataclasses import dataclass

from sycamore.models.enums import EdgeConfidence, EdgeType


@dataclass(frozen=True)
class AbilityEdge:
    id: str
    source_node_id: str
    target_node_id: str
    edge_type: EdgeType
    confidence: EdgeConfidence
    rationale: str | None
    created_at: str
