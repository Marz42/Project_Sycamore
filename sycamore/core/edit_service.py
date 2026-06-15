"""Structured editing guidance for AbilityNodes — Phase 2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import frontmatter

from sycamore.core.node_context import NodeContextError, load_node_context
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_parser import (
    replace_section,
)
from sycamore.storage.config_store import load_config
from sycamore.storage.markdown_writer import write_node_markdown
from sycamore.utils.paths import get_config_path, get_database_path, get_syca_home
from sycamore.review.factory import get_review_provider


class EditError(Exception):
    """Raised when edit cannot complete."""


# ── Block definitions per node type ──────────────────────────────────

_EDIT_BLOCKS: dict[str, list[tuple[str, str]]] = {
    "capability": [
        ("Core Idea", "用一句话解释这个能力解决什么问题，背后的机制是什么？"),
        ("Boundaries", "这个能力适合什么场景？不适合什么？最容易误用在哪里？"),
        ("Steps", "列出关键操作步骤（每行一个 `1. ` 开头）。"),
        ("Pitfalls", "记录踩过的坑或需要注意的陷阱。"),
        ("Cheatsheet", "粘贴命令、参数、配置片段等低频但实操必要的内容。"),
        ("Contrast", "与什么能力/命令容易混淆？如何区分？"),
        ("Minimal Task", "设计一个最小任务来验证自己真的掌握了：给定XX场景，你能完成YY操作。"),
    ],
    "concept": [
        ("Core Thesis", "这个理论/框架的核心主张是什么？用一两句话概括。"),
        ("Historical Context", "它出现的时代背景是什么？解决了当时什么问题？"),
        ("Critique", "它的局限是什么？有哪些反对观点或批判？"),
        ("Apply To", "找一个最近的真实事件，尝试用这个框架分析。格式：| 事件 | 分析 |"),
        ("Contrast", "与什么理论/框架容易混淆？关键区别是什么？"),
        ("Minimal Task", "设计一个最小任务：给定一个新事件，你能用这个框架写出分析。"),
    ],
    "theorem": [
        ("Formula", "写出公式（LaTeX 或纯文本均可）。"),
        ("Intuition", "用直觉语言解释这个公式，不要用数学符号。"),
        ("Boundary Conditions", "列出必须满足的前提条件和不适用的情况。"),
        ("Counterexamples", "构造或找一个真正违反边界的反例。格式：| 输入 | 为什么是反例 |"),
        ("Contrast", "与哪个定理容易混淆？如何区分？"),
        ("Minimal Task", "设计一个边界判断任务：给一个输入，判断定理是否适用。"),
    ],
    "process": [
        ("Mechanism", "描述系统如何工作——输入、输出、反馈回路。"),
        ("Parameters", "列出关键参数、正常范围和调节代价。格式：| 参数 | 含义 | 范围 | 代价 |"),
        ("Disturbance Response", "列出常见扰动及系统响应。格式：| 扰动 | 响应 | 风险 |"),
        ("Contrast", "与什么系统/机制容易混淆？如何区分？"),
        ("Minimal Task", "设计一个扰动场景：某个参数漂移了，判断系统能否稳定。"),
    ],
}

_SHARED_BLOCKS: list[tuple[str, str]] = [
    ("Contrast", "与什么容易混淆？如何区分？"),
    ("Minimal Task", "设计一个最小验证任务。"),
]


def get_edit_blocks(node_type: str) -> list[tuple[str, str]]:
    """Return ordered list of (block_name, prompt) for the given node type."""
    blocks = _EDIT_BLOCKS.get(node_type, _EDIT_BLOCKS["capability"])
    return list(blocks)


@dataclass(frozen=True)
class EditResult:
    node_id: str
    block: str
    written: bool


def edit_node_block(
    identifier: str,
    block_name: str,
    new_content: str,
    *,
    home: Path | None = None,
) -> EditResult:
    """Write new content into a specific block of a node's Markdown file."""
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        context = load_node_context(connection, identifier, home=root)

        # Read current Markdown
        text = context.node_file.read_text(encoding="utf-8")
        post = frontmatter.loads(text)
        metadata = dict(post.metadata)

        # Try to replace existing section, or insert new one before Practice Log
        try:
            new_body = replace_section(post.content, block_name, new_content)
        except ValueError:
            # Section doesn't exist yet — append before Practice Log
            new_body = _insert_section_before(
                post.content, block_name, new_content, "Practice Log"
            )

        # Write back
        content_hash, fm_hash = write_node_markdown(
            context.node_file,
            body=new_body,
            metadata=metadata,
        )

        # Update index
        from sycamore.storage.node_repository import upsert_node_index
        from sycamore.utils.time import utc_now_iso

        timestamp = utc_now_iso()
        upsert_node_index(
            connection,
            node_id=context.node.id,
            slug=context.node.slug,
            title=context.node.title,
            domain=context.node.domain,
            node_type=context.node.node_type,
            claimed_level=context.node.claimed_level,
            review_status=context.node.review_status,
            node_path=context.node.node_path,
            content_hash=content_hash,
            front_matter_hash=fm_hash,
            created_at=context.node.created_at,
            updated_at=timestamp,
            last_synced_at=timestamp,
        )

        return EditResult(node_id=context.node.id, block=block_name, written=True)
    except NodeContextError as error:
        raise EditError(str(error)) from error
    finally:
        connection.close()


def _insert_section_before(
    body: str, section_name: str, content: str, before_section: str
) -> str:
    """Insert a new ## section before another ## section."""
    marker = f"## {before_section}\n"
    idx = body.find(marker)
    if idx == -1:
        # Append at end
        return body.rstrip() + f"\n\n## {section_name}\n\n{content}\n"
    new_section = f"## {section_name}\n\n{content}\n\n"
    return body[:idx] + new_section + body[idx:]


def suggest_block_fill(
    node_title: str,
    node_type: str,
    domain: str | None,
    block_name: str,
    prompt_text: str,
    *,
    home: Path | None = None,
) -> str | None:
    """Ask the configured LLM provider for a fill suggestion for a block.
    
    Returns None if no provider is available or LLM is disabled.
    """
    root = home or get_syca_home()
    try:
        config = load_config(get_config_path(root))
        provider = get_review_provider(config)
    except Exception:
        return None

    system_prompt = (
        f"Node title: {node_title}\n"
        f"Node type: {node_type}\n"
        f"{'Domain: ' + domain if domain else ''}"
        f"Block to fill: {block_name}\n"
        f"Guidance: {prompt_text}\n\n"
        f"Provide a short, actionable suggestion that the user can edit."
    )
    try:
        result = provider.suggest_fill(system_prompt)
        if result.startswith("[Mock suggestion]") or result.startswith("[LLM unavailable"):
            return result
        return result
    except Exception:
        return None
