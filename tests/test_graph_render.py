from pathlib import Path

import pytest

from sycamore.core.capture_service import create_capture
from sycamore.core.graph_render import format_domain_graph_text
from sycamore.core.graph_service import build_domain_graph
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.link_service import create_link
from sycamore.core.promote_service import promote_capture
from sycamore.models.enums import CaptureKind, EdgeType
from sycamore.utils.paths import SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def _promote(home: Path, content: str, title: str) -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=content, home=home)
    result = promote_capture(capture.id, title=title, domain="shell", home=home)
    return result.node.id


def test_format_prerequisite_tree(syca_home: Path) -> None:
    cd_id = _promote(syca_home, "cd path", "我能切换目录")
    pwd_id = _promote(syca_home, "pwd", "我能查看当前目录")
    ls_id = _promote(syca_home, "ls -la", "我能列出目录详情")
    curl_id = _promote(syca_home, "curl url", "我能 curl")

    create_link(cd_id, pwd_id, edge_type=EdgeType.PREREQUISITE, home=syca_home)
    create_link(pwd_id, ls_id, edge_type=EdgeType.PREREQUISITE, home=syca_home)
    create_link(cd_id, curl_id, edge_type=EdgeType.RELATED, rationale="both CLI", home=syca_home)

    graph = build_domain_graph("shell", home=syca_home)
    lines = format_domain_graph_text(graph)
    text = "\n".join(lines)

    assert "Domain: shell (4 nodes, 3 links)" in text
    assert "[prerequisite]" in text
    assert "├──" in text or "└──" in text
    assert "我能切换目录" in text
    assert "我能列出目录详情" in text
    assert "[related]" in text
    assert "both CLI" in text
    assert "[unlinked]" not in text


def test_format_unlinked_nodes(syca_home: Path) -> None:
    _promote(syca_home, "a", "节点 A")
    graph = build_domain_graph("shell", home=syca_home)
    lines = format_domain_graph_text(graph)

    assert "No links yet" in "\n".join(lines)
    assert "节点 A" in "\n".join(lines)
