"""Markdown AbilityNode file generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import frontmatter

from sycamore.models.capture import CaptureItem
from sycamore.models.enums import CaptureKind, ClaimedLevel
from sycamore.storage.markdown_parser import split_markdown_document
from sycamore.utils.hash import sha256_hex


@dataclass(frozen=True)
class NodeMarkdownDraft:
    node_id: str
    slug: str
    title: str
    domain: str | None
    claimed_level: ClaimedLevel
    created_at: str
    updated_at: str
    body: str
    front_matter: dict[str, object]
    content_hash: str
    front_matter_hash: str


def _single_line(text: str, *, max_length: int = 120) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3]}..."


def default_title_from_capture(capture: CaptureItem) -> str:
    preview = _single_line(capture.content)
    if capture.kind is CaptureKind.CHEAT:
        return f"我能执行：{preview}"
    if capture.kind is CaptureKind.LINK:
        link = capture.source or capture.content
        return f"待查阅：{_single_line(link)}"
    return f"待整理：{preview}"


def _seed_body(capture: CaptureItem, title: str) -> str:
    context_block = ""
    if capture.context:
        context_block = f"\n\n捕获场景：{capture.context}"

    if capture.kind is CaptureKind.CHEAT:
        cheatsheet = capture.content.strip()
        capability = "我能把捕获的命令片段用于解决具体任务。"
    elif capture.kind is CaptureKind.LINK:
        link = (capture.source or capture.content).strip()
        cheatsheet = ""
        capability = f"我能查阅并运用该资料：{link}"
    else:
        cheatsheet = ""
        capability = capture.content.strip() or "用自己的话描述这项能力解决什么问题。"

    sections = [
        f"# {title}",
        "",
        "## Capability",
        "",
        capability + context_block,
        "",
        "## Mental Model",
        "",
        "### Core Idea",
        "",
        "用自己的话解释这个能力解决什么问题，以及背后的机制。",
        "",
        "### Boundaries",
        "",
        "- 适合什么场景。",
        "- 不适合什么场景。",
        "- 容易误用在哪里。",
        "",
        "## Cheatsheet",
        "",
    ]
    if cheatsheet:
        sections.append(cheatsheet)
        sections.append("")
    else:
        sections.append("只放低频但实操必要的命令、参数和配置。")
        sections.append("")

    if capture.kind is CaptureKind.LINK:
        link = (capture.source or capture.content).strip()
        sections.extend(
            [
                "## Practice Log",
                "",
                "### 记录",
                "",
                "- 场景：",
                "- 操作：",
                "- 结果：",
                "- 踩坑：",
                "",
                "## Review Notes",
                "",
                "只保存人类可读摘要和 ReviewRun ID。",
                "",
                "## References",
                "",
                f"- {link}",
            ]
        )
    else:
        sections.extend(
            [
                "## Practice Log",
                "",
                "### 记录",
                "",
                "- 场景：",
                "- 操作：",
                "- 结果：",
                "- 踩坑：",
                "",
                "## Review Notes",
                "",
                "只保存人类可读摘要和 ReviewRun ID。",
                "",
                "## References",
                "",
                "- 参考资料链接或本地资产路径。",
            ]
        )

    return "\n".join(sections)


def build_node_markdown_draft(
    *,
    capture: CaptureItem,
    node_id: str,
    slug: str,
    title: str,
    domain: str | None,
    claimed_level: ClaimedLevel,
    timestamp: str,
) -> NodeMarkdownDraft:
    body = _seed_body(capture, title)
    front_matter = {
        "id": node_id,
        "slug": slug,
        "title": title,
        "claimedLevel": claimed_level.value,
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }
    if domain:
        front_matter["domain"] = domain

    rendered = frontmatter.dumps(frontmatter.Post(body, **front_matter))
    front_matter_text, body_text = split_markdown_document(rendered)
    return NodeMarkdownDraft(
        node_id=node_id,
        slug=slug,
        title=title,
        domain=domain,
        claimed_level=claimed_level,
        created_at=timestamp,
        updated_at=timestamp,
        body=body_text,
        front_matter=front_matter,
        content_hash=sha256_hex(body_text),
        front_matter_hash=sha256_hex(front_matter_text),
    )


def render_node_markdown(draft: NodeMarkdownDraft) -> str:
    return frontmatter.dumps(frontmatter.Post(draft.body, **draft.front_matter))


def write_node_markdown(path: Path, draft: NodeMarkdownDraft) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_node_markdown(draft), encoding="utf-8")
    return path
