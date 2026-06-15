"""Clarify: interactive classification between capture and promote — Phase 2."""

from __future__ import annotations

from dataclasses import dataclass

from sycamore.models.capture import CaptureItem
from sycamore.models.enums import ClaimedLevel
from sycamore.storage.capture_repository import (
    CaptureRepositoryError,
    resolve_inbox_capture,
)
from sycamore.storage.database import open_initialized_database
from sycamore.utils.paths import get_database_path, get_syca_home
from pathlib import Path


class ClarifyError(Exception):
    """Raised when clarify cannot complete."""


@dataclass(frozen=True)
class ClarifySuggestion:
    capture: CaptureItem
    suggested_type: str
    suggested_title: str
    suggested_domain: str | None
    suggested_level: ClaimedLevel
    rationale: str


# ── Heuristic classification ─────────────────────────────────────────

_TYPE_KEYWORDS: dict[str, list[str]] = {
    "capability": [
        "命令", "操作", "步骤", "配置", "安装", "部署", "调试",
        "command", "cli", "bash", "shell", "git", "docker", "ssh",
    ],
    "concept": [
        "理论", "框架", "主义", "思想", "哲学", "经济学", "历史",
        "概念", "定义", "原理", "原则", "方法论", "paradigm",
    ],
    "theorem": [
        "定理", "公式", "推导", "证明", "引理", "推论", "公理",
        "数学", "算法", "复杂度", "收敛", "theorem", "lemma",
    ],
    "process": [
        "流程", "循环", "周期", "代谢", "反应", "传递", "转化",
        "机制", "回路", "反馈", "系统", "过程", "机理",
    ],
}

_DOMAIN_HINTS: dict[str, str] = {
    "shell": "shell",
    "bash": "shell",
    "linux": "shell",
    "docker": "devops",
    "k8s": "devops",
    "kubernetes": "devops",
    "git": "devops",
    "python": "programming",
    "rust": "programming",
    "sql": "data",
    "统计": "math",
    "数学": "math",
    "物理": "physics",
    "化学": "chemistry",
    "生物": "biology",
    "哲学": "philosophy",
    "历史": "history",
    "经济": "economics",
    "管理": "management",
}


def _guess_type(content: str) -> str:
    content_lower = content.lower()
    scores: dict[str, int] = {}
    for ntype, keywords in _TYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in content_lower)
        if score:
            scores[ntype] = score
    if not scores:
        return "capability"
    return max(scores, key=scores.get)


def _guess_domain(content: str, title: str) -> str | None:
    combined = (content + " " + title).lower()
    for hint, domain in _DOMAIN_HINTS.items():
        if hint in combined:
            return domain
    return None


def _guess_level(content: str) -> ClaimedLevel:
    content_lower = content.lower()
    if any(w in content_lower for w in ("理解", "懂了", "看懂了", "明白了", "了解了")):
        return ClaimedLevel.L1
    if any(w in content_lower for w in ("会用", "能写", "能配置", "能部署")):
        return ClaimedLevel.L2
    return ClaimedLevel.L0


def _guess_title(capture: CaptureItem) -> str:
    from sycamore.storage.markdown_store import default_title_from_capture
    return default_title_from_capture(capture)


def suggest_promotion(
    capture_id: str | None = None,
    *,
    home: Path | None = None,
) -> ClarifySuggestion:
    """Analyze a capture item and suggest promote parameters."""
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        try:
            capture = resolve_inbox_capture(
                connection, capture_id=capture_id, latest=True, index=None
            )
        except CaptureRepositoryError as error:
            raise ClarifyError(str(error)) from error

        suggested_type = _guess_type(capture.content)
        suggested_title = _guess_title(capture)
        suggested_domain = _guess_domain(capture.content, suggested_title)
        suggested_level = _guess_level(capture.content)

        rationales: list[str] = []
        if suggested_type != "capability":
            rationales.append(f"内容分析倾向于 {suggested_type} 类型")
        if suggested_domain:
            rationales.append(f"检测到领域关键词 → {suggested_domain}")

        return ClarifySuggestion(
            capture=capture,
            suggested_type=suggested_type,
            suggested_title=suggested_title,
            suggested_domain=suggested_domain,
            suggested_level=suggested_level,
            rationale="；".join(rationales) if rationales else "默认建议",
        )
    finally:
        connection.close()
