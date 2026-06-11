"""Shared node lookup helpers for core services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import sqlite3

from sycamore.models.ability_node import AbilityNode
from sycamore.storage.markdown_parser import ParsedNodeMarkdown, parse_node_markdown
from sycamore.storage.node_repository import NodeRepositoryError, resolve_node_identifier


class NodeContextError(Exception):
    """Raised when a node cannot be loaded for mutation."""


@dataclass(frozen=True)
class NodeContext:
    node: AbilityNode
    node_file: Path
    parsed: ParsedNodeMarkdown


def load_node_context(
    connection: sqlite3.Connection,
    identifier: str,
    *,
    home: Path,
) -> NodeContext:
    try:
        node = resolve_node_identifier(connection, identifier)
    except NodeRepositoryError as error:
        raise NodeContextError(str(error)) from error

    node_file = home / node.node_path
    if not node_file.exists():
        raise NodeContextError(f"Markdown file not found for node: {node.node_path}")

    parsed = parse_node_markdown(node_file)
    if parsed.missing_fields:
        raise NodeContextError(
            f"Markdown {node.node_path} is missing required fields: "
            f"{', '.join(parsed.missing_fields)}"
        )
    return NodeContext(node=node, node_file=node_file, parsed=parsed)
