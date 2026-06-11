from sycamore.storage.markdown_parser import extract_section, extract_sections, parse_node_markdown

SAMPLE = """\
---
id: "node-1"
slug: "shell-awk"
title: "我能用 awk 处理日志"
domain: "shell"
claimedLevel: "L1"
createdAt: "2026-06-11T00:00:00+00:00"
updatedAt: "2026-06-11T00:00:00+00:00"
---

# 我能用 awk 处理日志

## Capability

处理日志字段。

## Cheatsheet

awk '{print $1}' access.log

## Practice Log

### 记录

- 场景：
"""


def test_extract_sections_from_fixed_headers(tmp_path) -> None:
    path = tmp_path / "node.md"
    path.write_text(SAMPLE, encoding="utf-8")

    parsed = parse_node_markdown(path)

    assert parsed.node_id == "node-1"
    assert parsed.slug == "shell-awk"
    assert parsed.content_hash
    assert parsed.front_matter_hash
    assert extract_section(parsed.body, "Cheatsheet") == "awk '{print $1}' access.log"
    assert "Capability" in extract_sections(parsed.body)


def test_missing_front_matter_fields_are_reported(tmp_path) -> None:
    path = tmp_path / "broken.md"
    path.write_text("---\nslug: only-slug\n---\n\n# Body\n", encoding="utf-8")

    parsed = parse_node_markdown(path)

    assert "id" in parsed.missing_fields
    assert "title" in parsed.missing_fields
