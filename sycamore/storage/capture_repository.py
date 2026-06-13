"""Persistence for CaptureItem records."""

from __future__ import annotations

import sqlite3
import uuid

from sycamore.models.capture import CaptureItem
from sycamore.models.enums import CaptureKind, CaptureStatus, CapabilityEventType
from sycamore.utils.time import utc_now_iso


def _row_to_capture(row: sqlite3.Row) -> CaptureItem:
    return CaptureItem(
        id=row["id"],
        kind=CaptureKind(row["kind"]),
        content=row["content"],
        status=CaptureStatus(row["status"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        context=row["context"],
        source=row["source"],
        promoted_node_id=row["promoted_node_id"],
    )


def insert_capture(
    connection: sqlite3.Connection,
    *,
    kind: CaptureKind,
    content: str,
    context: str | None = None,
    source: str | None = None,
) -> CaptureItem:
    capture_id = str(uuid.uuid4())
    timestamp = utc_now_iso()
    connection.execute(
        """
        INSERT INTO capture_items (
            id, kind, content, context, source, status, promoted_node_id, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?);
        """,
        (
            capture_id,
            kind.value,
            content,
            context,
            source,
            CaptureStatus.INBOX.value,
            timestamp,
            timestamp,
        ),
    )
    connection.execute(
        """
        INSERT INTO capability_events (id, node_id, capture_id, type, payload_json, created_at)
        VALUES (?, NULL, ?, ?, NULL, ?);
        """,
        (
            str(uuid.uuid4()),
            capture_id,
            CapabilityEventType.CAPTURE_CREATED.value,
            timestamp,
        ),
    )
    connection.commit()
    row = connection.execute(
        "SELECT * FROM capture_items WHERE id = ?;",
        (capture_id,),
    ).fetchone()
    assert row is not None
    return _row_to_capture(row)


class CaptureRepositoryError(Exception):
    """Raised when capture persistence rules are violated."""


def get_capture_by_id(connection: sqlite3.Connection, capture_id: str) -> CaptureItem | None:
    row = connection.execute(
        "SELECT * FROM capture_items WHERE id = ?;",
        (capture_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_capture(row)


def mark_capture_promoted(
    connection: sqlite3.Connection,
    *,
    capture_id: str,
    node_id: str,
    timestamp: str,
) -> CaptureItem:
    updated = connection.execute(
        """
        UPDATE capture_items
        SET status = ?, promoted_node_id = ?, updated_at = ?
        WHERE id = ? AND status = ?;
        """,
        (
            CaptureStatus.PROMOTED.value,
            node_id,
            timestamp,
            capture_id,
            CaptureStatus.INBOX.value,
        ),
    ).rowcount
    if updated != 1:
        raise CaptureRepositoryError(f"Capture {capture_id} is not promotable from inbox.")

    row = connection.execute(
        "SELECT * FROM capture_items WHERE id = ?;",
        (capture_id,),
    ).fetchone()
    assert row is not None
    return _row_to_capture(row)


def list_inbox_captures(connection: sqlite3.Connection) -> list[CaptureItem]:
    rows = connection.execute(
        """
        SELECT * FROM capture_items
        WHERE status = ?
        ORDER BY created_at DESC;
        """,
        (CaptureStatus.INBOX.value,),
    ).fetchall()
    return [_row_to_capture(row) for row in rows]


def resolve_capture_identifier(connection: sqlite3.Connection, identifier: str) -> CaptureItem:
    exact = get_capture_by_id(connection, identifier)
    if exact is not None:
        if exact.status is not CaptureStatus.INBOX:
            raise CaptureRepositoryError(
                f"Capture {identifier} has status '{exact.status.value}' and cannot be promoted."
            )
        return exact

    prefix_matches = connection.execute(
        """
        SELECT * FROM capture_items
        WHERE id LIKE ? AND status = ?
        ORDER BY created_at DESC;
        """,
        (f"{identifier}%", CaptureStatus.INBOX.value),
    ).fetchall()
    if len(prefix_matches) == 1:
        return _row_to_capture(prefix_matches[0])
    if len(prefix_matches) > 1:
        raise CaptureRepositoryError(
            f"Capture identifier '{identifier}' matches multiple inbox items. "
            "Use a longer prefix, --index, or --latest."
        )

    raise CaptureRepositoryError(f"Capture not found in inbox: {identifier}")


def resolve_inbox_capture(
    connection: sqlite3.Connection,
    *,
    capture_id: str | None = None,
    latest: bool = False,
    index: int | None = None,
) -> CaptureItem:
    selectors = sum(
        1
        for value in (
            capture_id is not None,
            latest,
            index is not None,
        )
        if value
    )
    if selectors > 1:
        raise CaptureRepositoryError("Use only one of capture id, --latest, or --index.")

    if latest or (capture_id is None and index is None):
        items = list_inbox_captures(connection)
        if not items:
            raise CaptureRepositoryError("Inbox is empty. Nothing to promote.")
        return items[0]

    if index is not None:
        if index < 1:
            raise CaptureRepositoryError("--index must be 1 or greater.")
        items = list_inbox_captures(connection)
        if not items:
            raise CaptureRepositoryError("Inbox is empty. Nothing to promote.")
        if index > len(items):
            raise CaptureRepositoryError(
                f"Inbox index {index} is out of range. Current inbox has {len(items)} item(s)."
            )
        return items[index - 1]

    assert capture_id is not None
    return resolve_capture_identifier(connection, capture_id)
