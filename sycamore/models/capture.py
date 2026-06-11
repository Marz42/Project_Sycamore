"""CaptureItem domain model."""

from __future__ import annotations

from dataclasses import dataclass

from sycamore.models.enums import CaptureKind, CaptureStatus


@dataclass(frozen=True)
class CaptureItem:
    id: str
    kind: CaptureKind
    content: str
    status: CaptureStatus
    created_at: str
    updated_at: str
    context: str | None = None
    source: str | None = None
    promoted_node_id: str | None = None
