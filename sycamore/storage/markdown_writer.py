"""Write updates back to AbilityNode Markdown files."""

from __future__ import annotations

from pathlib import Path

import frontmatter

from sycamore.storage.markdown_parser import compute_hashes, replace_section
from sycamore.utils.time import utc_now_iso

PRACTICE_LOG_SECTION = "Practice Log"


def format_practice_entry(
    *,
    timestamp: str,
    scenario: str | None = None,
    action: str | None = None,
    result: str | None = None,
    pitfall: str | None = None,
) -> str:
    lines = [f"### {timestamp}", ""]
    if scenario:
        lines.append(f"- 场景：{scenario}")
    if action:
        lines.append(f"- 操作：{action}")
    if result:
        lines.append(f"- 结果：{result}")
    if pitfall:
        lines.append(f"- 踩坑：{pitfall}")
    return "\n".join(lines)


def append_practice_log(body: str, entry: str) -> str:
    from sycamore.storage.markdown_parser import extract_section

    existing = extract_section(body, PRACTICE_LOG_SECTION) or ""
    merged = f"{entry}\n\n{existing}".strip() if existing else entry
    return replace_section(body, PRACTICE_LOG_SECTION, merged)


def write_node_markdown(
    path: Path,
    *,
    body: str,
    metadata: dict[str, object],
) -> tuple[str, str]:
    timestamp = utc_now_iso()
    metadata = dict(metadata)
    metadata["updatedAt"] = timestamp
    rendered = frontmatter.dumps(frontmatter.Post(body, **metadata))
    path.write_text(rendered, encoding="utf-8")
    content_hash, front_matter_hash = compute_hashes(rendered)
    return content_hash, front_matter_hash
