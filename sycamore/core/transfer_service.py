"""Transfer/application layer — Phase 3: variant scenarios, boundary tests, composition tasks."""

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


class TransferLevel(StrEnum):
    A = "A"  # variant recognition
    B = "B"  # boundary judgment
    C = "C"  # composition task
    D = "D"  # real scenario


class TransferOutcome(StrEnum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAIL = "fail"


LEVEL_DESCRIPTIONS: dict[TransferLevel, str] = {
    TransferLevel.A: "变式识别 — 换一种说法描述同一个能力",
    TransferLevel.B: "边界判断 — 判断某个场景是否适用该能力",
    TransferLevel.C: "组合任务 — 多个节点协作解决一个问题",
    TransferLevel.D: "真实场景 — 噪声信息多、考点不明示",
}


class TransferError(Exception):
    """Raised when transfer operations fail."""


@dataclass(frozen=True)
class TransferScenario:
    node: AbilityNode
    level: TransferLevel
    description: str
    scenario: str


@dataclass(frozen=True)
class TransferResult:
    node: AbilityNode
    level: TransferLevel
    outcome: TransferOutcome
    recorded_at: str


# ── Scenario generation ──────────────────────────────────────────────


def _build_scenario_prompt(node: AbilityNode, body: str, level: TransferLevel) -> str:
    mental_model = (extract_section(body, "Mental Model") or "").strip()
    cheatsheet = (extract_section(body, "Cheatsheet") or "").strip()
    node_info = (
        f"Node title: {node.title}\n"
        f"Domain: {node.domain or '(none)'}\n"
        f"Node type: {node.node_type}\n"
    )
    if mental_model:
        node_info += f"Mental Model summary: {mental_model[:300]}\n"
    if cheatsheet:
        node_info += f"Cheatsheet: {cheatsheet[:200]}\n"

    level_instructions = {
        TransferLevel.A: (
            "Generate a variant recognition question: describe a scenario that "
            "requires the SAME capability but using DIFFERENT words. Do NOT name "
            "the node title or the command. The user must recognize which capability to use. "
            "Output ONLY the scenario description, 1-3 sentences."
        ),
        TransferLevel.B: (
            "Generate a boundary judgment question: describe a scenario that is "
            "CLOSE to the node's capability but where the capability does NOT apply, "
            "or where it MIGHT apply but needs caution. Ask 'would you use this? why/why not?'. "
            "Output ONLY the scenario and question, 2-4 sentences."
        ),
        TransferLevel.C: (
            "Generate a composition task: describe a multi-step scenario that requires "
            "this capability PLUS other generic skills (navigating directories, searching, "
            "filtering). Do NOT name the specific commands. Output ONLY the task description, 2-4 sentences."
        ),
        TransferLevel.D: (
            "Generate a realistic troubleshooting scenario with noise: describe a problem "
            "that involves this capability but also includes irrelevant details. The user "
            "must identify what's relevant and what's noise. Output ONLY the scenario, 3-5 sentences."
        ),
    }

    return (
        f"{level_instructions[level]}\n\n{node_info}"
    )


def generate_scenario(
    identifier: str,
    level: TransferLevel = TransferLevel.A,
    *,
    home: Path | None = None,
) -> TransferScenario:
    """Generate a transfer scenario for a node at the given level."""
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        context = load_node_context(connection, identifier, home=root)

        # Try LLM first, fall back to template
        scenario = _try_llm_scenario(context.node, context.parsed.body, level, root)
        if scenario is None:
            scenario = _template_scenario(context.node, level)

        return TransferScenario(
            node=context.node,
            level=level,
            description=LEVEL_DESCRIPTIONS[level],
            scenario=scenario,
        )
    except NodeContextError as error:
        raise TransferError(str(error)) from error
    finally:
        connection.close()


def _try_llm_scenario(
    node: AbilityNode, body: str, level: TransferLevel, root: Path
) -> str | None:
    try:
        from sycamore.review.factory import get_review_provider
        from sycamore.storage.config_store import load_config
        from sycamore.utils.paths import get_config_path

        config = load_config(get_config_path(root))
        provider = get_review_provider(config)
        prompt = _build_scenario_prompt(node, body, level)
        result = provider.suggest_fill(prompt)
        if result and not result.startswith("[Mock suggestion]") and not result.startswith("[LLM unavailable"):
            return result.strip()
    except Exception:
        pass
    return None


def _template_scenario(node: AbilityNode, level: TransferLevel) -> str:
    title = node.title
    if level == TransferLevel.A:
        return (
            f"假设你需要完成一个与「{title}」相关的任务，但你的同事用完全不同的措辞描述了这个需求。"
            f"请你想一想：这个能力到底解决什么问题？换个说法描述它。"
        )
    elif level == TransferLevel.B:
        return (
            f"你正在做一个任务，表面上看起来需要「{title}」的能力。"
            f"但深入分析后，你发现这个场景其实不适合用这个能力——或者需要非常小心。"
            f"请解释：为什么不适合？边界在哪里？"
        )
    elif level == TransferLevel.C:
        return (
            f"你需要完成一个复杂任务：进入指定目录 → 查看文件列表 → 找到相关文件 → 提取关键信息。"
            f"其中一步需要用到「{title}」。请描述：你会如何组合多个能力来完成这个任务？"
        )
    else:
        return (
            f"生产环境中出现了一个奇怪的问题。日志显示大量错误，但错误信息被其他进程的输出淹没了。"
            f"你需要排查根因。请描述你会如何利用「{title}」及相关能力来诊断问题。"
            f"注意：场景中有大量无关信息，你需要自行判断哪些是噪声。"
        )


# ── Outcome recording ────────────────────────────────────────────────


def record_transfer_outcome(
    identifier: str,
    level: TransferLevel,
    outcome: TransferOutcome,
    *,
    note: str | None = None,
    home: Path | None = None,
) -> TransferResult:
    """Record the user's self-assessed outcome for a transfer drill."""
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        context = load_node_context(connection, identifier, home=root)
        timestamp = utc_now_iso()

        event_map = {
            TransferOutcome.SUCCESS: CapabilityEventType.TRANSFER_SUCCESS,
            TransferOutcome.PARTIAL: CapabilityEventType.TRANSFER_PARTIAL,
            TransferOutcome.FAIL: CapabilityEventType.TRANSFER_FAIL,
        }
        event_type = event_map[outcome]

        payload: dict[str, object] = {
            "level": level.value,
            "outcome": outcome.value,
        }
        if note:
            payload["note"] = note

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
        return TransferResult(
            node=context.node,
            level=level,
            outcome=outcome,
            recorded_at=timestamp,
        )
    except NodeContextError as error:
        raise TransferError(str(error)) from error
    finally:
        connection.close()


def get_transfer_count(
    identifier: str,
    *,
    home: Path | None = None,
) -> dict[str, int]:
    """Get transfer success/partial/fail counts for a node."""
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        context = load_node_context(connection, identifier, home=root)
        counts: dict[str, int] = {"success": 0, "partial": 0, "fail": 0}
        for ot in ("success", "partial", "fail"):
            row = connection.execute(
                """
                SELECT COUNT(*) FROM capability_events
                WHERE node_id = ? AND type = ?;
                """,
                (context.node.id, f"transfer_{ot}"),
            ).fetchone()
            if row:
                counts[ot] = row[0]
        return counts
    except NodeContextError as error:
        raise TransferError(str(error)) from error
    finally:
        connection.close()
