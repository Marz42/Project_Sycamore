"""Node status and freshness views."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sycamore.core.freshness import DEFAULT_STALE_AFTER_DAYS, NodeFreshness, assess_node_freshness
from sycamore.models.ability_node import AbilityNode
from sycamore.storage.config_store import load_config
from sycamore.storage.database import open_initialized_database
from sycamore.storage.node_repository import list_all_nodes, list_nodes_by_domain
from sycamore.utils.paths import get_config_path, get_database_path, get_syca_home
from sycamore.models.enums import CapabilityEventType


@dataclass(frozen=True)
class StaleNodesReport:
    stale_after_days: int
    nodes: tuple[NodeFreshness, ...]


@dataclass(frozen=True)
class DomainStatusEntry:
    node: AbilityNode
    freshness: NodeFreshness


@dataclass(frozen=True)
class DomainStatusReport:
    domain: str
    stale_after_days: int
    entries: tuple[DomainStatusEntry, ...]


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


def list_domain_status(
    domain: str,
    *,
    home: Path | None = None,
    stale_after_days: int | None = None,
    now: datetime | None = None,
) -> DomainStatusReport:
    root = home or get_syca_home()
    threshold = stale_after_days if stale_after_days is not None else _stale_after_days(root)
    connection = open_initialized_database(get_database_path(root))
    try:
        nodes = list_nodes_by_domain(connection, domain)
        if not nodes:
            raise ValueError(f"No nodes found in domain '{domain}'.")
        entries: list[DomainStatusEntry] = []
        for node in nodes:
            freshness = assess_node_freshness(
                connection,
                node,
                stale_after_days=threshold,
                now=now,
            )
            entries.append(DomainStatusEntry(node=node, freshness=freshness))
        entries.sort(key=lambda item: (item.freshness.is_stale, item.node.title), reverse=True)
        return DomainStatusReport(domain=domain, stale_after_days=threshold, entries=tuple(entries))
    finally:
        connection.close()


# ── Weakness analysis ────────────────────────────────────────────────


@dataclass(frozen=True)
class WeakNode:
    node: AbilityNode
    fail_count: int
    top_fail_type: str | None
    risk_level: str  # "high" | "medium" | "low"


@dataclass(frozen=True)
class WeaknessReport:
    nodes: tuple[WeakNode, ...]
    total_fails: int


def list_weak_nodes(
    *,
    home: Path | None = None,
    min_fails: int = 1,
) -> WeaknessReport:
    """Analyze failure patterns across nodes. Returns nodes sorted by fail count desc."""
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        nodes = list_all_nodes(connection)
        weak_nodes: list[WeakNode] = []
        total_fails = 0

        for node in nodes:
            rows = connection.execute(
                """
                SELECT payload_json FROM capability_events
                WHERE node_id = ? AND type = ?
                ORDER BY created_at;
                """,
                (node.id, CapabilityEventType.RECOVERY_FAILED.value),
            ).fetchall()

            if not rows:
                continue

            fail_count = len(rows)
            total_fails += fail_count

            fail_types: dict[str, int] = {}
            for row in rows:
                if row["payload_json"]:
                    try:
                        payload = json.loads(row["payload_json"])
                        ft = payload.get("failType")
                        if ft:
                            fail_types[ft] = fail_types.get(ft, 0) + 1
                    except json.JSONDecodeError:
                        continue

            top_fail_type = max(fail_types, key=fail_types.get) if fail_types else None

            if fail_count >= 5:
                risk_level = "high"
            elif fail_count >= 3:
                risk_level = "medium"
            else:
                risk_level = "low"

            if fail_count >= min_fails:
                weak_nodes.append(
                    WeakNode(
                        node=node,
                        fail_count=fail_count,
                        top_fail_type=top_fail_type,
                        risk_level=risk_level,
                    )
                )

        weak_nodes.sort(key=lambda w: w.fail_count, reverse=True)
        return WeaknessReport(nodes=tuple(weak_nodes), total_fails=total_fails)
    finally:
        connection.close()
