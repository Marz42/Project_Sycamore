"""Promote CaptureItem into AbilityNode."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from sycamore.models.ability_node import AbilityNode
from sycamore.models.capture import CaptureItem
from sycamore.models.enums import (
    CapabilityEventType,
    ClaimedLevel,
    ReviewStatus,
)
from sycamore.storage.capture_repository import (
    CaptureRepositoryError,
    mark_capture_promoted,
    resolve_inbox_capture,
)
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_store import (
    build_node_markdown_draft,
    default_title_from_capture,
    write_node_markdown,
)
from sycamore.storage.node_repository import insert_ability_node, slug_exists
from sycamore.utils.paths import NODES_DIRNAME, get_database_path, get_nodes_dir, get_syca_home
from sycamore.utils.slug import slugify
from sycamore.utils.time import utc_now_iso


class PromoteError(Exception):
    """Raised when promote cannot complete."""


@dataclass(frozen=True)
class PromoteResult:
    capture: CaptureItem
    node: AbilityNode
    node_file: Path


def _reserve_unique_slug(connection, base_slug: str) -> str:
    if not slug_exists(connection, base_slug):
        return base_slug
    suffix = 2
    while slug_exists(connection, f"{base_slug}-{suffix}"):
        suffix += 1
    return f"{base_slug}-{suffix}"


def promote_capture(
    capture_id: str | None = None,
    *,
    latest: bool = False,
    index: int | None = None,
    title: str | None = None,
    domain: str | None = None,
    node_type: str = "capability",
    claimed_level: ClaimedLevel = ClaimedLevel.L0,
    home: Path | None = None,
) -> PromoteResult:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        try:
            capture = resolve_inbox_capture(
                connection,
                capture_id=capture_id,
                latest=latest,
                index=index,
            )
        except CaptureRepositoryError as error:
            raise PromoteError(str(error)) from error

        node_id = str(uuid.uuid4())
        node_title = title or default_title_from_capture(capture)
        base_slug = slugify(node_title)
        if base_slug == "untitled-node":
            base_slug = f"node-{node_id[:8]}"
        slug = _reserve_unique_slug(connection, base_slug)
        timestamp = utc_now_iso()
        relative_node_path = f"{NODES_DIRNAME}/{slug}.md"
        node_file = get_nodes_dir(root) / f"{slug}.md"

        draft = build_node_markdown_draft(
            capture=capture,
            node_id=node_id,
            slug=slug,
            title=node_title,
            domain=domain,
            node_type=node_type,
            claimed_level=claimed_level,
            timestamp=timestamp,
        )
        write_node_markdown(node_file, draft)

        try:
            with connection:
                node = insert_ability_node(
                    connection,
                    node_id=node_id,
                    slug=slug,
                    title=node_title,
                    domain=domain,
                    node_type=node_type,
                    claimed_level=claimed_level,
                    review_status=ReviewStatus.NOT_REVIEWED,
                    node_path=relative_node_path,
                    content_hash=draft.content_hash,
                    front_matter_hash=draft.front_matter_hash,
                    created_at=timestamp,
                    updated_at=timestamp,
                )
                updated_capture = mark_capture_promoted(
                    connection,
                    capture_id=capture.id,
                    node_id=node_id,
                    timestamp=timestamp,
                )
                connection.execute(
                    """
                    INSERT INTO capability_events (
                        id, node_id, capture_id, type, payload_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (
                        str(uuid.uuid4()),
                        node_id,
                        capture.id,
                        CapabilityEventType.CAPTURE_PROMOTED.value,
                        json.dumps({"slug": slug, "title": node_title}, ensure_ascii=False),
                        timestamp,
                    ),
                )
        except Exception:
            if node_file.exists():
                node_file.unlink()
            raise

        return PromoteResult(
            capture=updated_capture,
            node=node,
            node_file=node_file,
        )
    except CaptureRepositoryError as error:
        raise PromoteError(str(error)) from error
    finally:
        connection.close()
