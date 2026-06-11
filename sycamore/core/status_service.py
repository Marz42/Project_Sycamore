"""Node status and freshness views."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sycamore.core.freshness import DEFAULT_STALE_AFTER_DAYS, NodeFreshness, assess_node_freshness
from sycamore.storage.config_store import load_config
from sycamore.storage.database import open_initialized_database
from sycamore.storage.node_repository import list_all_nodes
from sycamore.utils.paths import get_config_path, get_database_path, get_syca_home


@dataclass(frozen=True)
class StaleNodesReport:
    stale_after_days: int
    nodes: tuple[NodeFreshness, ...]


def _stale_after_days(home: Path) -> int:
    config = load_config(get_config_path(home))
    freshness = config.get("freshness", {})
    if isinstance(freshness, dict):
        value = freshness.get("stale_after_days")
        if isinstance(value, int) and value >= 0:
            return value
    return DEFAULT_STALE_AFTER_DAYS


def list_stale_nodes(
    *,
    home: Path | None = None,
    stale_after_days: int | None = None,
    now: datetime | None = None,
) -> StaleNodesReport:
    root = home or get_syca_home()
    threshold = stale_after_days if stale_after_days is not None else _stale_after_days(root)
    connection = open_initialized_database(get_database_path(root))
    try:
        stale_nodes: list[NodeFreshness] = []
        for node in list_all_nodes(connection):
            freshness = assess_node_freshness(
                connection,
                node,
                stale_after_days=threshold,
                now=now,
            )
            if freshness.is_stale:
                stale_nodes.append(freshness)
        stale_nodes.sort(key=lambda item: item.days_since_activity, reverse=True)
        return StaleNodesReport(stale_after_days=threshold, nodes=tuple(stale_nodes))
    finally:
        connection.close()
