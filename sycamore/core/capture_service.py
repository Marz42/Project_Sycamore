"""Capture and Inbox use cases."""

from __future__ import annotations

from pathlib import Path

from sycamore.models.capture import CaptureItem
from sycamore.models.enums import CaptureKind
from sycamore.storage.capture_repository import insert_capture, list_inbox_captures
from sycamore.storage.database import open_initialized_database
from sycamore.utils.paths import get_database_path, get_syca_home


def create_capture(
    *,
    kind: CaptureKind,
    content: str,
    context: str | None = None,
    source: str | None = None,
    home: Path | None = None,
) -> CaptureItem:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        return insert_capture(
            connection,
            kind=kind,
            content=content,
            context=context,
            source=source,
        )
    finally:
        connection.close()


def list_inbox(*, home: Path | None = None) -> list[CaptureItem]:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        return list_inbox_captures(connection)
    finally:
        connection.close()
