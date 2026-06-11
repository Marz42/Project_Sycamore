"""Update claimed level on AbilityNodes."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from sycamore.core.node_context import NodeContextError, load_node_context
from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import CapabilityEventType, ClaimedLevel
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_writer import write_node_markdown
from sycamore.storage.node_repository import upsert_node_index
from sycamore.utils.paths import get_database_path, get_syca_home
from sycamore.utils.time import utc_now_iso


class LevelError(Exception):
    """Raised when level update cannot complete."""


@dataclass(frozen=True)
class LevelSetResult:
    node: AbilityNode
    previous_level: ClaimedLevel
    new_level: ClaimedLevel


def set_claimed_level(
    identifier: str,
    level: ClaimedLevel,
    *,
    home: Path | None = None,
) -> LevelSetResult:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        context = load_node_context(connection, identifier, home=root)
        previous_level = context.node.claimed_level
        if previous_level == level:
            raise LevelError(f"Node already has claimed level {level.value}.")

        post = frontmatter.loads(context.node_file.read_text(encoding="utf-8"))
        metadata = dict(post.metadata)
        metadata["claimedLevel"] = level.value
        timestamp = utc_now_iso()
        content_hash, front_matter_hash = write_node_markdown(
            context.node_file,
            body=context.parsed.body,
            metadata=metadata,
        )
        post_after = frontmatter.loads(context.node_file.read_text(encoding="utf-8"))

        with connection:
            node, _ = upsert_node_index(
                connection,
                node_id=context.node.id,
                slug=str(post_after.metadata["slug"]),
                title=str(post_after.metadata["title"]),
                domain=str(post_after.metadata["domain"])
                if post_after.metadata.get("domain")
                else None,
                claimed_level=level,
                review_status=context.node.review_status,
                node_path=context.node.node_path,
                content_hash=content_hash,
                front_matter_hash=front_matter_hash,
                created_at=str(post_after.metadata["createdAt"]),
                updated_at=str(post_after.metadata["updatedAt"]),
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
                    CapabilityEventType.MANUAL_LEVEL_CHANGED.value,
                    json.dumps(
                        {"previousLevel": previous_level.value, "newLevel": level.value},
                        ensure_ascii=False,
                    ),
                    timestamp,
                ),
            )
        return LevelSetResult(node=node, previous_level=previous_level, new_level=level)
    except NodeContextError as error:
        raise LevelError(str(error)) from error
    finally:
        connection.close()
