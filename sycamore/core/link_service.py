"""Create manual ability relationships."""

from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path

from sycamore.models.ability_edge import AbilityEdge
from sycamore.models.enums import EdgeConfidence, EdgeType
from sycamore.storage.database import open_initialized_database
from sycamore.storage.edge_repository import insert_edge
from sycamore.storage.node_repository import NodeRepositoryError, resolve_node_identifier
from sycamore.utils.paths import get_database_path, get_syca_home
from sycamore.utils.time import utc_now_iso


class LinkError(Exception):
    """Raised when a link cannot be created."""


@dataclass(frozen=True)
class LinkResult:
    edge: AbilityEdge
    source_title: str
    target_title: str


def create_link(
    source_identifier: str,
    target_identifier: str,
    *,
    edge_type: EdgeType = EdgeType.PREREQUISITE,
    confidence: EdgeConfidence = EdgeConfidence.EXPLICIT,
    rationale: str | None = None,
    home: Path | None = None,
) -> LinkResult:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        try:
            source = resolve_node_identifier(connection, source_identifier)
            target = resolve_node_identifier(connection, target_identifier)
        except NodeRepositoryError as error:
            raise LinkError(str(error)) from error

        if source.id == target.id:
            raise LinkError("Source and target must be different nodes.")

        timestamp = utc_now_iso()
        with connection:
            try:
                edge = insert_edge(
                    connection,
                    edge_id=str(uuid.uuid4()),
                    source_node_id=source.id,
                    target_node_id=target.id,
                    edge_type=edge_type,
                    confidence=confidence,
                    rationale=rationale,
                    created_at=timestamp,
                )
            except sqlite3.IntegrityError as error:
                raise LinkError(
                    f"Link already exists: {source.slug} -[{edge_type.value}]-> {target.slug}"
                ) from error
        return LinkResult(edge=edge, source_title=source.title, target_title=target.title)
    finally:
        connection.close()
