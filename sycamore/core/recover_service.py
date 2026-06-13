"""Recovery drill use cases."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from sycamore.core.node_context import NodeContextError, load_node_context
from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import CapabilityEventType
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_parser import extract_section
from sycamore.utils.paths import get_database_path, get_syca_home
from sycamore.utils.time import utc_now_iso

MENTAL_MODEL_SECTION = "Mental Model"
CHEATSHEET_SECTION = "Cheatsheet"
_CHEATSHEET_PLACEHOLDER = "只放低频但实操必要的命令、参数和配置。"


class RecoverError(Exception):
    """Raised when recovery drill cannot run."""


@dataclass(frozen=True)
class RecoveryDrill:
    node: AbilityNode
    node_file: Path
    mental_model: str
    cheatsheet: str | None
    is_stale: bool
    days_since_activity: int


@dataclass(frozen=True)
class RecoveryResult:
    node: AbilityNode
    passed: bool
    recorded_at: str


def _cheatsheet_from_body(body: str) -> str | None:
    content = extract_section(body, CHEATSHEET_SECTION)
    if content is None:
        return None
    stripped = content.strip()
    if not stripped or stripped == _CHEATSHEET_PLACEHOLDER:
        return None
    return stripped


def preview_recovery_drill(
    identifier: str,
    *,
    home: Path | None = None,
    stale_after_days: int | None = None,
) -> RecoveryDrill:
    from sycamore.core.freshness import assess_node_freshness
    from sycamore.core.status_service import _stale_after_days

    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        context = load_node_context(connection, identifier, home=root)
        mental_model = extract_section(context.parsed.body, MENTAL_MODEL_SECTION)
        if mental_model is None:
            raise RecoverError("Node is missing a Mental Model section.")

        threshold = stale_after_days if stale_after_days is not None else _stale_after_days(root)
        freshness = assess_node_freshness(
            connection,
            context.node,
            stale_after_days=threshold,
        )
        return RecoveryDrill(
            node=context.node,
            node_file=context.node_file,
            mental_model=mental_model.strip(),
            cheatsheet=_cheatsheet_from_body(context.parsed.body),
            is_stale=freshness.is_stale,
            days_since_activity=freshness.days_since_activity,
        )
    except NodeContextError as error:
        raise RecoverError(str(error)) from error
    finally:
        connection.close()


def record_recovery_outcome(
    identifier: str,
    *,
    passed: bool,
    note: str | None = None,
    home: Path | None = None,
) -> RecoveryResult:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        context = load_node_context(connection, identifier, home=root)
        timestamp = utc_now_iso()
        event_type = (
            CapabilityEventType.RECOVERY_PASSED
            if passed
            else CapabilityEventType.RECOVERY_FAILED
        )
        with connection:
            connection.execute(
                """
                INSERT INTO capability_events (id, node_id, capture_id, type, payload_json, created_at)
                VALUES (?, ?, NULL, ?, ?, ?);
                """,
                (
                    str(uuid.uuid4()),
                    context.node.id,
                    event_type.value,
                    json.dumps({"note": note}, ensure_ascii=False) if note else None,
                    timestamp,
                ),
            )
        return RecoveryResult(node=context.node, passed=passed, recorded_at=timestamp)
    except NodeContextError as error:
        raise RecoverError(str(error)) from error
    finally:
        connection.close()
