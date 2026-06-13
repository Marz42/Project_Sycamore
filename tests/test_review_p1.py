import json
from pathlib import Path
from unittest.mock import patch

import frontmatter
import pytest
from typer.testing import CliRunner

from sycamore.cli.app import app
from sycamore.core.capture_service import create_capture
from sycamore.core.init_service import initialize_sycamore
from sycamore.core.promote_service import promote_capture
from sycamore.core.review_service import (
    ReviewError,
    decide_review,
    list_node_reviews,
    preview_review,
    run_review,
)
from sycamore.models.enums import CaptureKind, ReviewStatus, UserDecision
from sycamore.review.provider import HttpReviewProvider
from sycamore.utils.paths import SYCA_HOME_ENV


@pytest.fixture
def syca_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "sycamore-home"
    monkeypatch.setenv(SYCA_HOME_ENV, str(home))
    initialize_sycamore(home)
    return home


def _promote_with_mental_model(home: Path, cheat: str, title: str, mental_model: str) -> str:
    capture = create_capture(kind=CaptureKind.CHEAT, content=cheat, home=home)
    result = promote_capture(capture.id, title=title, home=home)
    node_file = result.node_file
    text = node_file.read_text(encoding="utf-8")
    updated = text.replace(
        "用自己的话解释这个能力解决什么问题，以及背后的机制。",
        mental_model,
    )
    node_file.write_text(updated, encoding="utf-8")
    return result.node.id


def test_list_node_reviews_marks_outdated_after_mental_model_change(syca_home: Path) -> None:
    node_id = _promote_with_mental_model(
        syca_home,
        "git status",
        "我能查看 Git 状态",
        "git status 显示工作区与暂存区变更。",
    )
    review = run_review(node_id, home=syca_home).review_run

    node_file = next((syca_home / "nodes").glob("*.md"))
    text = node_file.read_text(encoding="utf-8")
    node_file.write_text(
        text.replace(
            "git status 显示工作区与暂存区变更。",
            "git status 还能显示当前分支名。",
        ),
        encoding="utf-8",
    )

    summaries = list_node_reviews(node_id, home=syca_home)
    assert len(summaries) == 1
    assert summaries[0].review.id == review.id
    assert summaries[0].is_outdated is True


def test_decide_review_updates_user_decision_and_node_status(syca_home: Path) -> None:
    node_id = _promote_with_mental_model(
        syca_home,
        "pytest -q",
        "我能运行测试",
        "pytest 收集并执行测试用例。",
    )
    review_id = run_review(node_id, home=syca_home).review_run.id

    result = decide_review(review_id, UserDecision.ACCEPTED, home=syca_home)

    assert result.review.user_decision is UserDecision.ACCEPTED
    assert result.node.review_status is ReviewStatus.ACCEPTED_BY_USER


def test_review_rejects_llm_allowed_false(syca_home: Path) -> None:
    node_id = _promote_with_mental_model(
        syca_home,
        "curl example.com",
        "我能发起 HTTP 请求",
        "curl 可以查看 HTTP 响应头和正文。",
    )
    node_file = next((syca_home / "nodes").glob("*.md"))
    post = frontmatter.load(node_file)
    post.metadata["llmAllowed"] = False
    node_file.write_text(frontmatter.dumps(post), encoding="utf-8")

    with pytest.raises(ReviewError, match="llmAllowed"):
        preview_review(node_id, home=syca_home)


def test_http_review_provider_parses_json_response() -> None:
    from sycamore.review.prompt import build_review_payload

    provider = HttpReviewProvider(endpoint="http://example.com/review")
    review_payload = build_review_payload(
        node_id="node-1",
        node_title="title",
        node_slug="slug",
        domain="shell",
        claimed_level="L1",
        mental_model="core idea",
        mental_model_hash="abc",
    )
    response_body = json.dumps(
        {
            "summary": "HTTP critique",
            "factIssues": ["fact"],
            "boundaryIssues": ["boundary"],
            "questions": ["question"],
            "practiceSuggestions": ["practice"],
            "model": "remote-v1",
        }
    ).encode("utf-8")

    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.read.return_value = response_body
        critique = provider.critique(review_payload)

    assert critique.summary == "HTTP critique"
    assert critique.model == "remote-v1"


def test_review_list_and_decide_cli_flow(syca_home: Path) -> None:
    node_id = _promote_with_mental_model(
        syca_home,
        "uv sync",
        "我能同步依赖",
        "uv sync 安装 pyproject 中声明的依赖。",
    )
    runner = CliRunner()

    run_result = runner.invoke(app, ["review", node_id])
    assert run_result.exit_code == 0

    list_result = runner.invoke(app, ["reviews", "list", node_id])
    assert list_result.exit_code == 0
    assert "Review Runs" in list_result.output

    review_id = list_node_reviews(node_id, home=syca_home)[0].review.id
    accept_result = runner.invoke(app, ["reviews", "accept", review_id])
    assert accept_result.exit_code == 0
    assert "Accepted review" in accept_result.output
