"""Unit tests for utility modules and config_store."""

from pathlib import Path


from sycamore.storage.config_store import load_config, write_default_config
from sycamore.utils.hash import sha256_hex
from sycamore.utils.slug import slugify
from sycamore.utils.time import utc_now_iso


# ── hash ─────────────────────────────────────────────────────────────


def test_sha256_hex_consistent() -> None:
    assert sha256_hex("hello") == sha256_hex("hello")


def test_sha256_hex_different() -> None:
    assert sha256_hex("hello") != sha256_hex("world")


def test_sha256_hex_length() -> None:
    assert len(sha256_hex("test")) == 64


def test_sha256_hex_empty() -> None:
    assert len(sha256_hex("")) == 64


# ── slug ─────────────────────────────────────────────────────────────


def test_slugify_english() -> None:
    assert slugify("Hello World") == "hello-world"


def test_slugify_with_special_chars() -> None:
    assert slugify("hello!@#world") == "hello-world"


def test_slugify_chinese_fallback() -> None:
    result = slugify("你好世界")
    assert result == "untitled-node"  # falls back when no latin chars


def test_slugify_mixed() -> None:
    result = slugify("Docker 容器部署")
    assert "docker" in result


def test_slugify_multiple_spaces() -> None:
    assert slugify("a   b") == "a-b"


# ── time ─────────────────────────────────────────────────────────────


def test_utc_now_iso_format() -> None:
    ts = utc_now_iso()
    assert "T" in ts
    assert "+" in ts or "Z" in ts


def test_utc_now_iso_monotonic() -> None:
    t1 = utc_now_iso()
    t2 = utc_now_iso()
    assert t1 <= t2


# ── config_store ─────────────────────────────────────────────────────


def test_load_config_from_nonexistent_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "nonexistent.toml"
    config = load_config(path)
    assert isinstance(config, dict)
    assert config == {}


def test_write_and_load_config_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    write_default_config(path)
    assert path.exists()

    config = load_config(path)
    assert isinstance(config, dict)
    assert config["llm"]["enabled"] is False


def test_load_config_preserves_existing(tmp_path: Path) -> None:
    path = tmp_path / "custom.toml"
    path.write_text("[freshness]\nstale_after_days = 14\n", encoding="utf-8")

    config = load_config(path)
    assert config["freshness"]["stale_after_days"] == 14
