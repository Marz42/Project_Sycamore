"""Synchronize Markdown AbilityNodes into SQLite index."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import CapabilityEventType, ReviewStatus
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_parser import parse_node_markdown
from sycamore.storage.node_repository import upsert_node_index
from sycamore.utils.paths import get_database_path, get_nodes_dir, get_syca_home
from sycamore.utils.time import utc_now_iso


class SyncError(Exception):
    """Raised when sync cannot complete."""


@dataclass(frozen=True)
class SyncResult:
    synced: int
    created: int
    updated: int
    skipped: int
    nodes: tuple[AbilityNode, ...]


def _relative_node_path(home: Path, markdown_path: Path) -> str:
    return markdown_path.relative_to(home).as_posix()


def sync_nodes(*, home: Path | None = None) -> SyncResult:
    root = home or get_syca_home()
    nodes_dir = get_nodes_dir(root)
    if not nodes_dir.exists():
        return SyncResult(synced=0, created=0, updated=0, skipped=0, nodes=())

    connection = open_initialized_database(get_database_path(root))
    created_count = 0
    updated_count = 0
    skipped_count = 0
    synced_nodes: list[AbilityNode] = []

    try:
        markdown_files = sorted(nodes_dir.glob("*.md"))
        with connection:
            for markdown_path in markdown_files:
                parsed = parse_node_markdown(markdown_path)
                if parsed.missing_fields:
                    skipped_count += 1
                    continue

                node_path = _relative_node_path(root, markdown_path)
                timestamp = utc_now_iso()
                node, created = upsert_node_index(
                    connection,
                    node_id=parsed.node_id,
                    slug=parsed.slug,
                    title=parsed.title,
                    domain=parsed.domain,
                    claimed_level=parsed.claimed_level,
                    review_status=ReviewStatus.NOT_REVIEWED,
                    node_path=node_path,
                    content_hash=parsed.content_hash,
                    front_matter_hash=parsed.front_matter_hash,
                    created_at=parsed.created_at,
                    updated_at=parsed.updated_at,
                    last_synced_at=timestamp,
                )
                connection.execute(
                    """
                    INSERT INTO capability_events (id, node_id, capture_id, type, payload_json, created_at)
                    VALUES (?, ?, NULL, ?, ?, ?);
                    """,
                    (
                        str(uuid.uuid4()),
                        node.id,
                        CapabilityEventType.NODE_SYNCED.value,
                        json.dumps({"nodePath": node_path}, ensure_ascii=False),
                        timestamp,
                    ),
                )
                synced_nodes.append(node)
                if created:
                    created_count += 1
                else:
                    updated_count += 1
        return SyncResult(
            synced=len(synced_nodes),
            created=created_count,
            updated=updated_count,
            skipped=skipped_count,
            nodes=tuple(synced_nodes),
        )
    finally:
        connection.close()
