"""Derive node freshness from CapabilityEvents and timestamps."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import CapabilityEventType

DEFAULT_STALE_AFTER_DAYS = 30

FRESHNESS_ACTIVITY_TYPES = (
    CapabilityEventType.PRACTICE_LOGGED.value,
    CapabilityEventType.CHEATSHEET_QUERIED.value,
    CapabilityEventType.REVIEW_COMPLETED.value,
    CapabilityEventType.RECOVERY_PASSED.value,
    CapabilityEventType.MANUAL_LEVEL_CHANGED.value,
)


@dataclass(frozen=True)
class NodeFreshness:
    node: AbilityNode
    last_activity_at: str
    days_since_activity: int
    is_stale: bool


def _parse_iso(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def get_last_activity_at(connection: sqlite3.Connection, node: AbilityNode) -> str:
    placeholders = ", ".join("?" for _ in FRESHNESS_ACTIVITY_TYPES)
    row = connection.execute(
        f"""
        SELECT MAX(created_at) AS last_at
        FROM capability_events
        WHERE node_id = ? AND type IN ({placeholders});
        """,
        (node.id, *FRESHNESS_ACTIVITY_TYPES),
    ).fetchone()
    event_time = row["last_at"] if row is not None else None
    candidates = [node.created_at]
    if event_time:
        candidates.append(event_time)
    return max(candidates, key=_parse_iso)


def assess_node_freshness(
    connection: sqlite3.Connection,
    node: AbilityNode,
    *,
    stale_after_days: int = DEFAULT_STALE_AFTER_DAYS,
    now: datetime | None = None,
) -> NodeFreshness:
    reference = now or datetime.now(UTC)
    last_activity_at = get_last_activity_at(connection, node)
    last_activity = _parse_iso(last_activity_at)
    if last_activity.tzinfo is None:
        last_activity = last_activity.replace(tzinfo=UTC)
    delta = reference - last_activity.astimezone(UTC)
    days_since = max(delta.days, 0)
    is_stale = delta > timedelta(days=stale_after_days)
    return NodeFreshness(
        node=node,
        last_activity_at=last_activity_at,
        days_since_activity=days_since,
        is_stale=is_stale,
    )
