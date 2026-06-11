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
