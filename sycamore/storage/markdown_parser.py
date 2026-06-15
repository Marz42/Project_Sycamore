"""Parse AbilityNode Markdown files and fixed sections."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from sycamore.models.enums import ClaimedLevel
from sycamore.utils.hash import sha256_hex

REQUIRED_FRONT_MATTER_FIELDS = ("id", "slug", "title", "claimedLevel", "createdAt", "updatedAt")

_SECTION_PATTERN = re.compile(
    r"^## (.+?)\s*$\n(.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)


@dataclass(frozen=True)
class ParsedNodeMarkdown:
    path: Path
    node_id: str
    slug: str
    title: str
    domain: str | None
    node_type: str
    claimed_level: ClaimedLevel
    created_at: str
    updated_at: str
    body: str
    content_hash: str
    front_matter_hash: str
    sections: dict[str, str]
    missing_fields: tuple[str, ...]


def split_markdown_document(text: str) -> tuple[str, str]:
    _, front_matter_text, body_text = text.split("---", 2)
    return front_matter_text.strip(), body_text.lstrip("\n")


def compute_hashes(text: str) -> tuple[str, str]:
    front_matter_text, body_text = split_markdown_document(text)
    return sha256_hex(body_text), sha256_hex(front_matter_text)


def extract_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    for match in _SECTION_PATTERN.finditer(body):
        name = match.group(1).strip()
        content = match.group(2).strip()
        sections[name] = content
    return sections


def extract_section(body: str, section_name: str) -> str | None:
    sections = extract_sections(body)
    return sections.get(section_name)


def replace_section(body: str, section_name: str, new_content: str) -> str:
    pattern = re.compile(
        rf"(^## {re.escape(section_name)}\s*$\n)(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise ValueError(f"Section not found: {section_name}")
    return pattern.sub(lambda m: f"{m.group(1)}{new_content.rstrip()}\n\n", body, count=1)


def missing_required_fields(metadata: dict[str, object]) -> tuple[str, ...]:
    return tuple(field for field in REQUIRED_FRONT_MATTER_FIELDS if field not in metadata)


def parse_node_markdown(path: Path) -> ParsedNodeMarkdown:
    text = path.read_text(encoding="utf-8")
    post = frontmatter.loads(text)
    metadata = dict(post.metadata)
    missing = missing_required_fields(metadata)

    if missing:
        return ParsedNodeMarkdown(
            path=path,
            node_id=str(metadata.get("id", "")),
            slug=str(metadata.get("slug", "")),
            title=str(metadata.get("title", "")),
            domain=str(metadata["domain"]) if metadata.get("domain") else None,
            node_type=str(metadata.get("type", "capability")),
            claimed_level=ClaimedLevel.L0,
            created_at=str(metadata.get("createdAt", "")),
            updated_at=str(metadata.get("updatedAt", "")),
            body=post.content,
            content_hash="",
            front_matter_hash="",
            sections={},
            missing_fields=missing,
        )

    body_text = post.content
    content_hash, front_matter_hash = compute_hashes(text)
    sections = extract_sections(body_text)

    return ParsedNodeMarkdown(
        path=path,
        node_id=str(metadata["id"]),
        slug=str(metadata["slug"]),
        title=str(metadata["title"]),
        domain=str(metadata["domain"]) if metadata.get("domain") else None,
        node_type=str(metadata.get("type", "capability")),
        claimed_level=ClaimedLevel(str(metadata["claimedLevel"])),
        created_at=str(metadata["createdAt"]),
        updated_at=str(metadata["updatedAt"]),
        body=body_text,
        content_hash=content_hash,
        front_matter_hash=front_matter_hash,
        sections=sections,
        missing_fields=missing,
    )
