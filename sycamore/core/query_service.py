"""Query promoted AbilityNodes."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from sycamore.core.sync_service import sync_nodes
from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import CapabilityEventType
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_parser import extract_section, parse_node_markdown
from sycamore.storage.node_repository import list_all_nodes
from sycamore.utils.paths import get_database_path, get_syca_home
from sycamore.utils.time import utc_now_iso

CHEATSHEET_SECTION = "Cheatsheet"
_PLACEHOLDER_SNIPPETS = (
    "只放低频但实操必要的命令、参数和配置。",
)


@dataclass(frozen=True)
class CheatsheetMatch:
    node: AbilityNode
    cheatsheet: str
    node_file: Path


def _is_meaningful_cheatsheet(content: str | None) -> bool:
    if not content:
        return False
    stripped = content.strip()
    if not stripped:
        return False
    return stripped not in _PLACEHOLDER_SNIPPETS


def _node_matches_term(node: AbilityNode, cheatsheet: str | None, term: str) -> bool:
    needle = term.casefold()
    haystacks = (node.title, node.slug, cheatsheet or "")
    return any(needle in value.casefold() for value in haystacks if value)


def query_cheatsheet(term: str, *, home: Path | None = None) -> list[CheatsheetMatch]:
    root = home or get_syca_home()
    sync_nodes(home=root)

    connection = open_initialized_database(get_database_path(root))
    matches: list[CheatsheetMatch] = []

    try:
        nodes = list_all_nodes(connection)
        for node in nodes:
            node_file = root / node.node_path
            if not node_file.exists():
                continue

            parsed = parse_node_markdown(node_file)
            cheatsheet = extract_section(parsed.body, CHEATSHEET_SECTION)
            if not _node_matches_term(node, cheatsheet, term):
                continue

            matches.append(
                CheatsheetMatch(
                    node=node,
                    cheatsheet=cheatsheet or "",
                    node_file=node_file,
                )
            )

        if matches:
            timestamp = utc_now_iso()
            with connection:
                for match in matches:
                    connection.execute(
                        """
                        INSERT INTO capability_events (
                            id, node_id, capture_id, type, payload_json, created_at
                        ) VALUES (?, ?, NULL, ?, ?, ?);
                        """,
                        (
                            str(uuid.uuid4()),
                            match.node.id,
                            CapabilityEventType.CHEATSHEET_QUERIED.value,
                            json.dumps({"term": term}, ensure_ascii=False),
                            timestamp,
                        ),
                    )
        return matches
    finally:
        connection.close()
