"""Append Practice Log entries to AbilityNodes."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from sycamore.core.node_context import NodeContextError, load_node_context
from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import CapabilityEventType
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_writer import append_practice_log, format_practice_entry, write_node_markdown
from sycamore.storage.node_repository import upsert_node_index
from sycamore.utils.paths import get_database_path, get_syca_home
from sycamore.utils.time import utc_now_iso


class PracticeError(Exception):
    """Raised when practice logging cannot complete."""


@dataclass(frozen=True)
class PracticeResult:
    node: AbilityNode
    node_file: Path
    entry_timestamp: str


def log_practice(
    identifier: str,
    *,
    note: str | None = None,
    scenario: str | None = None,
    action: str | None = None,
    result: str | None = None,
    pitfall: str | None = None,
    home: Path | None = None,
) -> PracticeResult:
    if not any((note, scenario, action, result, pitfall)):
        raise PracticeError("Provide at least one of --note, --scenario, --action, --result, or --pitfall.")

    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        context = load_node_context(connection, identifier, home=root)
        timestamp = utc_now_iso()
        entry = format_practice_entry(
            timestamp=timestamp,
            scenario=scenario,
            action=action or note,
            result=result,
            pitfall=pitfall,
        )
        updated_body = append_practice_log(context.parsed.body, entry)
        post = frontmatter.loads(context.node_file.read_text(encoding="utf-8"))
        content_hash, front_matter_hash = write_node_markdown(
            context.node_file,
            body=updated_body,
            metadata=dict(post.metadata),
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
                claimed_level=context.node.claimed_level,
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
                    CapabilityEventType.PRACTICE_LOGGED.value,
                    json.dumps(
                        {
                            "scenario": scenario,
                            "action": action or note,
                            "result": result,
                            "pitfall": pitfall,
                        },
                        ensure_ascii=False,
                    ),
                    timestamp,
                ),
            )
        return PracticeResult(node=node, node_file=context.node_file, entry_timestamp=timestamp)
    except NodeContextError as error:
        raise PracticeError(str(error)) from error
    finally:
        connection.close()
