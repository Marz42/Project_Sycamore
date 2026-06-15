"""Recovery drill use cases — Phase 1A: recall-first + fail-type + ratings."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from enum import StrEnum
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


class RecoverMode(StrEnum):
    RECALL_FIRST = "recall-first"
    SUPPORTED = "supported"
    FULL = "full"


class RecoverRating(StrEnum):
    FAIL = "fail"
    HARD = "hard"
    PASS = "pass"
    EASY = "easy"


class FailType(StrEnum):
    RECALL = "recall"
    CONCEPT = "concept"
    PROCEDURE = "procedure"
    TRANSFER = "transfer"


# ── NodeType-aware recall prompts ────────────────────────────────────

_RECALL_PROMPTS: dict[str, str] = {
    "capability": "不看资料，第一步做什么？完整的操作步骤是什么？",
    "concept": "不看资料，这个理论/框架的核心主张是什么？",
    "theorem": "不看资料，这个定理的公式和直觉含义是什么？",
    "process": "不看资料，这个系统的机理是什么？关键参数有哪些？",
}


def _recall_prompt(node_type: str) -> str:
    return _RECALL_PROMPTS.get(node_type, _RECALL_PROMPTS["capability"])


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
    node_type: str
    recall_prompt: str


@dataclass(frozen=True)
class RecoveryResult:
    node: AbilityNode
    passed: bool
    rating: str
    fail_type: str | None
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
    mode: RecoverMode = RecoverMode.RECALL_FIRST,
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
            node_type=context.node.node_type,
            recall_prompt=_recall_prompt(context.node.node_type),
        )
    except NodeContextError as error:
        raise RecoverError(str(error)) from error
    finally:
        connection.close()


def record_recovery_outcome(
    identifier: str,
    *,
    passed: bool | None = None,
    rating: RecoverRating | None = None,
    fail_type: FailType | None = None,
    note: str | None = None,
    home: Path | None = None,
) -> RecoveryResult:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        context = load_node_context(connection, identifier, home=root)
        timestamp = utc_now_iso()

        if rating is not None:
            effective_rating = rating.value
            effective_passed = rating != RecoverRating.FAIL
        elif passed is not None:
            effective_rating = RecoverRating.PASS.value if passed else RecoverRating.FAIL.value
            effective_passed = passed
        else:
            raise RecoverError("Either --pass/--fail or --hard/--easy must be specified.")

        event_type = (
            CapabilityEventType.RECOVERY_PASSED
            if effective_passed
            else CapabilityEventType.RECOVERY_FAILED
        )
        payload: dict[str, object] = {"rating": effective_rating}
        if note:
            payload["note"] = note
        if fail_type and not effective_passed:
            payload["failType"] = fail_type.value

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
                    json.dumps(payload, ensure_ascii=False),
                    timestamp,
                ),
            )
        return RecoveryResult(
            node=context.node,
            passed=effective_passed,
            rating=effective_rating,
            fail_type=fail_type.value if fail_type else None,
            recorded_at=timestamp,
        )
    except NodeContextError as error:
        raise RecoverError(str(error)) from error
    finally:
        connection.close()
