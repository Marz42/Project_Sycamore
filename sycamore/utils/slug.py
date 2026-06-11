"""Slug helpers for AbilityNode filenames."""

from __future__ import annotations

import re
import unicodedata

_SLUG_INVALID = re.compile(r"[^a-z0-9]+")
_DEFAULT_SLUG = "untitled-node"


def slugify(value: str, *, max_length: int = 80) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = _SLUG_INVALID.sub("-", ascii_text.lower()).strip("-")
    if not slug:
        slug = _DEFAULT_SLUG
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    return slug or _DEFAULT_SLUG
