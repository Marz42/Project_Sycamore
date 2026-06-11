"""Persistence for AbilityNode records."""

from __future__ import annotations

import sqlite3

from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import ClaimedLevel, ReviewStatus


def _row_to_node(row: sqlite3.Row) -> AbilityNode:
    return AbilityNode(
        id=row["id"],
        slug=row["slug"],
        title=row["title"],
        domain=row["domain"],
        claimed_level=ClaimedLevel(row["claimed_level"]),
        review_status=ReviewStatus(row["review_status"]),
        node_path=row["node_path"],
        content_hash=row["content_hash"],
        front_matter_hash=row["front_matter_hash"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        last_synced_at=row["last_synced_at"],
    )


def slug_exists(connection: sqlite3.Connection, slug: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM ability_nodes WHERE slug = ? LIMIT 1;",
        (slug,),
    ).fetchone()
    return row is not None


def list_all_nodes(connection: sqlite3.Connection) -> list[AbilityNode]:
    rows = connection.execute(
        "SELECT * FROM ability_nodes ORDER BY title COLLATE NOCASE;"
    ).fetchall()
    return [_row_to_node(row) for row in rows]


def get_node_by_id(connection: sqlite3.Connection, node_id: str) -> AbilityNode | None:
    row = connection.execute(
        "SELECT * FROM ability_nodes WHERE id = ?;",
        (node_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_node(row)


class NodeRepositoryError(Exception):
    """Raised when node lookup rules are violated."""


def resolve_node_identifier(connection: sqlite3.Connection, identifier: str) -> AbilityNode:
    exact = get_node_by_id(connection, identifier)
    if exact is not None:
        return exact

    by_slug = get_node_by_slug(connection, identifier)
    if by_slug is not None:
        return by_slug

    prefix_matches = connection.execute(
        "SELECT * FROM ability_nodes WHERE id LIKE ?;",
        (f"{identifier}%",),
    ).fetchall()
    if len(prefix_matches) == 1:
        return _row_to_node(prefix_matches[0])
    if len(prefix_matches) > 1:
        raise NodeRepositoryError(
            f"Node identifier '{identifier}' matches multiple nodes. Use a longer prefix or slug."
        )

    raise NodeRepositoryError(f"Node not found: {identifier}")


def update_review_status(
    connection: sqlite3.Connection,
    node_id: str,
    review_status: ReviewStatus,
) -> None:
    connection.execute(
        "UPDATE ability_nodes SET review_status = ? WHERE id = ?;",
        (review_status.value, node_id),
    )


def get_node_by_slug(connection: sqlite3.Connection, slug: str) -> AbilityNode | None:
    row = connection.execute(
        "SELECT * FROM ability_nodes WHERE slug = ?;",
        (slug,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_node(row)


def upsert_node_index(
    connection: sqlite3.Connection,
    *,
    node_id: str,
    slug: str,
    title: str,
    domain: str | None,
    claimed_level: ClaimedLevel,
    review_status: ReviewStatus,
    node_path: str,
    content_hash: str,
    front_matter_hash: str,
    created_at: str,
    updated_at: str,
    last_synced_at: str,
) -> tuple[AbilityNode, bool]:
    """Insert or update a node index row. Returns (node, created)."""
    existing = get_node_by_id(connection, node_id)
    if existing is None:
        connection.execute(
            """
            INSERT INTO ability_nodes (
                id, slug, title, domain, claimed_level, review_status,
                node_path, content_hash, front_matter_hash, created_at, updated_at, last_synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                node_id,
                slug,
                title,
                domain,
                claimed_level.value,
                review_status.value,
                node_path,
                content_hash,
                front_matter_hash,
                created_at,
                updated_at,
                last_synced_at,
            ),
        )
        created = True
    else:
        # review_status stays in SQLite; sync only refreshes Markdown-derived fields.
        connection.execute(
            """
            UPDATE ability_nodes
            SET slug = ?, title = ?, domain = ?, claimed_level = ?,
                node_path = ?, content_hash = ?, front_matter_hash = ?,
                updated_at = ?, last_synced_at = ?
            WHERE id = ?;
            """,
            (
                slug,
                title,
                domain,
                claimed_level.value,
                node_path,
                content_hash,
                front_matter_hash,
                updated_at,
                last_synced_at,
                node_id,
            ),
        )
        created = False

    row = connection.execute(
        "SELECT * FROM ability_nodes WHERE id = ?;",
        (node_id,),
    ).fetchone()
    assert row is not None
    return _row_to_node(row), created


def insert_ability_node(
    connection: sqlite3.Connection,
    *,
    node_id: str,
    slug: str,
    title: str,
    domain: str | None,
    claimed_level: ClaimedLevel,
    review_status: ReviewStatus,
    node_path: str,
    content_hash: str,
    front_matter_hash: str,
    created_at: str,
    updated_at: str,
) -> AbilityNode:
    connection.execute(
        """
        INSERT INTO ability_nodes (
            id, slug, title, domain, claimed_level, review_status,
            node_path, content_hash, front_matter_hash, created_at, updated_at, last_synced_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            node_id,
            slug,
            title,
            domain,
            claimed_level.value,
            review_status.value,
            node_path,
            content_hash,
            front_matter_hash,
            created_at,
            updated_at,
            created_at,
        ),
    )
    row = connection.execute(
        "SELECT * FROM ability_nodes WHERE id = ?;",
        (node_id,),
    ).fetchone()
    assert row is not None
    return _row_to_node(row)
