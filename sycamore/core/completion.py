"""Node completion state assessment — Phase 2."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from sycamore.storage.markdown_parser import ParsedNodeMarkdown


class CompletionState(StrEnum):
    DRAFT = "draft"
    MODELED = "modeled"
    CONTRASTED = "contrasted"
    REVIEWABLE = "reviewable"


# ── Placeholder detection ────────────────────────────────────────────

_PLACEHOLDER_PATTERNS = [
    "用自己的话解释",
    "只放低频但实操必要",
    "参考资料链接或本地资产路径",
    "- 场景：",
    "- 操作：",
    "- 结果：",
    "- 踩坑：",
    "它出现的时代背景",
    "这个理论/框架的核心主张是什么",
    "用数学语言表述",
    "用直觉语言解释这个定理",
    "描述系统如何工作",
]


def _is_placeholder(text: str | None) -> bool:
    if text is None:
        return True
    stripped = text.strip()
    if not stripped:
        return True
    for pattern in _PLACEHOLDER_PATTERNS:
        if pattern in stripped:
            return True
    return False


# ── Required blocks per type for each state ──────────────────────────

_CORE_IDEA_KEYS = ("Core Idea",)
_PROBLEM_KEYS = ("Problem", "Problem It Solves")
_BOUNDARIES_KEYS = ("Boundaries",)
_CONTRAST_KEYS = ("Contrast",)
_MINIMAL_TASK_KEYS = ("Minimal Task",)
_CHEATSHEET_KEYS = ("Cheatsheet",)


def _has_content(body: str, sections: dict[str, str], keys: tuple[str, ...]) -> bool:
    """Check if any of the named sections (h2 or h3) have non-placeholder content."""
    for key in keys:
        content = sections.get(key)
        if content and not _is_placeholder(content):
            return True
    # Also check h3 sub-sections by searching the full body
    for key in keys:
        if _has_h3_section(body, key):
            return True
    return False


def _has_h3_section(body: str, name: str) -> bool:
    """Check if body contains ### {name} with non-placeholder content."""
    import re
    pattern = re.compile(
        rf"^###\s+{re.escape(name)}\s*$\n(.*?)(?=^##|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match:
        return not _is_placeholder(match.group(1).strip())
    return False


@dataclass(frozen=True)
class CompletionReport:
    state: CompletionState
    missing: tuple[str, ...]
    node_id: str
    node_title: str


def assess_completion(parsed: ParsedNodeMarkdown) -> CompletionReport:
    sections = parsed.sections
    missing: list[str] = []

    body = parsed.body
    has_core = _has_content(body, sections, _CORE_IDEA_KEYS)
    has_problem = _has_content(body, sections, _PROBLEM_KEYS)
    has_boundaries = _has_content(body, sections, _BOUNDARIES_KEYS)
    has_contrast = _has_content(body, sections, _CONTRAST_KEYS)
    has_task = _has_content(body, sections, _MINIMAL_TASK_KEYS)
    has_cheatsheet = _has_content(body, sections, _CHEATSHEET_KEYS)

    if not has_core:
        missing.append("Core Idea")
    if not has_problem:
        missing.append("Problem It Solves")
    if not has_boundaries:
        missing.append("Boundaries")
    if not has_task:
        missing.append("Minimal Task")
    if not has_contrast:
        missing.append("Contrast")
    if not has_cheatsheet:
        missing.append("Cheatsheet")

    if not has_core:
        state = CompletionState.DRAFT
    elif has_contrast and has_cheatsheet:
        state = CompletionState.REVIEWABLE
    elif has_contrast:
        state = CompletionState.CONTRASTED
    elif has_core and has_problem and has_boundaries and has_task:
        state = CompletionState.MODELED
    else:
        state = CompletionState.DRAFT

    return CompletionReport(
        state=state,
        missing=tuple(missing),
        node_id=parsed.node_id,
        node_title=parsed.title,
    )


def is_draft(parsed: ParsedNodeMarkdown) -> bool:
    return assess_completion(parsed).state == CompletionState.DRAFT
