"""Persistence for AbilityEdge records."""

from __future__ import annotations

import sqlite3

from sycamore.models.ability_edge import AbilityEdge
from sycamore.models.enums import EdgeConfidence, EdgeType


def _row_to_edge(row: sqlite3.Row) -> AbilityEdge:
    return AbilityEdge(
        id=row["id"],
        source_node_id=row["source_node_id"],
        target_node_id=row["target_node_id"],
        edge_type=EdgeType(row["type"]),
        confidence=EdgeConfidence(row["confidence"]),
        rationale=row["rationale"],
        created_at=row["created_at"],
    )


def insert_edge(
    connection: sqlite3.Connection,
    *,
    edge_id: str,
    source_node_id: str,
    target_node_id: str,
    edge_type: EdgeType,
    confidence: EdgeConfidence,
    rationale: str | None,
    created_at: str,
) -> AbilityEdge:
    connection.execute(
        """
        INSERT INTO ability_edges (
            id, source_node_id, target_node_id, type, confidence, rationale, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        (
            edge_id,
            source_node_id,
            target_node_id,
            edge_type.value,
            confidence.value,
            rationale,
            created_at,
        ),
    )
    row = connection.execute(
        "SELECT * FROM ability_edges WHERE id = ?;",
        (edge_id,),
    ).fetchone()
    assert row is not None
    return _row_to_edge(row)


class EdgeRepositoryError(Exception):
    """Raised when edge persistence rules are violated."""


def list_edges_for_domain(
    connection: sqlite3.Connection,
    domain: str,
) -> list[AbilityEdge]:
    rows = connection.execute(
        """
        SELECT e.*
        FROM ability_edges e
        JOIN ability_nodes source ON source.id = e.source_node_id
        JOIN ability_nodes target ON target.id = e.target_node_id
        WHERE source.domain = ? AND target.domain = ?
        ORDER BY e.created_at;
        """,
        (domain, domain),
    ).fetchall()
    return [_row_to_edge(row) for row in rows]


def list_edges_touching_nodes(
    connection: sqlite3.Connection,
    node_ids: set[str],
) -> list[AbilityEdge]:
    if not node_ids:
        return []
    placeholders = ",".join("?" for _ in node_ids)
    rows = connection.execute(
        f"""
        SELECT * FROM ability_edges
        WHERE source_node_id IN ({placeholders})
           OR target_node_id IN ({placeholders})
        ORDER BY created_at;
        """,
        tuple(node_ids) + tuple(node_ids),
    ).fetchall()
    return [_row_to_edge(row) for row in rows]
