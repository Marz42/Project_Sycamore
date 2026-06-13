"""Review use cases with mock-first Provider."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import CapabilityEventType, ReviewStatus, UserDecision
from sycamore.models.review_run import ReviewRun
from sycamore.review.factory import get_review_provider
from sycamore.review.prompt import PROMPT_VERSION, ReviewPayload, build_review_payload
from sycamore.review.provider import ReviewProvider, dumps_critique_raw
from sycamore.storage.config_store import load_config
from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_parser import extract_section, parse_node_markdown
from sycamore.storage.node_repository import (
    NodeRepositoryError,
    resolve_node_identifier,
    update_review_status,
)
from sycamore.storage.review_repository import (
    ReviewRepositoryError,
    insert_review_run,
    list_reviews_for_node,
    resolve_review_identifier,
    update_user_decision,
)
from sycamore.utils.hash import sha256_hex
from sycamore.utils.paths import REVIEWS_DIRNAME, get_config_path, get_database_path, get_reviews_dir, get_syca_home
from sycamore.utils.time import utc_now_iso

MENTAL_MODEL_SECTION = "Mental Model"
_CORE_IDEA_PLACEHOLDER = "用自己的话解释这个能力解决什么问题，以及背后的机制。"


class ReviewError(Exception):
    """Raised when review cannot complete."""


@dataclass(frozen=True)
class ReviewPreview:
    node: AbilityNode
    payload: ReviewPayload
    node_file: Path
    provider_name: str


@dataclass(frozen=True)
class ReviewResult:
    node: AbilityNode
    review_run: ReviewRun
    raw_output_file: Path


@dataclass(frozen=True)
class ReviewRunSummary:
    review: ReviewRun
    is_outdated: bool


@dataclass(frozen=True)
class ReviewDecisionResult:
    review: ReviewRun
    node: AbilityNode


def _core_idea_from_mental_model(mental_model: str) -> str:
    lines = mental_model.splitlines()
    collecting = False
    chunks: list[str] = []
    for line in lines:
        if line.strip() == "### Core Idea":
            collecting = True
            continue
        if collecting and line.startswith("### "):
            break
        if collecting and line.strip():
            chunks.append(line.strip())
    if chunks:
        return "\n".join(chunks)
    return mental_model.strip()


def _mental_model_from_body(body: str) -> str:
    content = extract_section(body, MENTAL_MODEL_SECTION)
    if content is None:
        raise ReviewError("Node is missing a Mental Model section.")
    core_idea = _core_idea_from_mental_model(content)
    if not core_idea or core_idea == _CORE_IDEA_PLACEHOLDER:
        raise ReviewError("Mental Model is still placeholder text. Write your own understanding first.")
    return content.strip()


def _ensure_llm_allowed(node_file: Path) -> None:
    post = frontmatter.load(node_file)
    if post.metadata.get("llmAllowed") is False:
        raise ReviewError("LLM review is disabled for this node (llmAllowed: false).")


def _load_review_context(
    connection,
    identifier: str,
    *,
    home: Path,
) -> tuple[AbilityNode, Path, str, str]:
    try:
        node = resolve_node_identifier(connection, identifier)
    except NodeRepositoryError as error:
        raise ReviewError(str(error)) from error

    node_file = home / node.node_path
    if not node_file.exists():
        raise ReviewError(f"Markdown file not found for node: {node.node_path}")

    _ensure_llm_allowed(node_file)
    parsed = parse_node_markdown(node_file)
    mental_model_section = _mental_model_from_body(parsed.body)
    core_idea = _core_idea_from_mental_model(mental_model_section)
    mental_model_hash = sha256_hex(core_idea)
    return node, node_file, core_idea, mental_model_hash


def _resolve_provider(home: Path, provider: ReviewProvider | None) -> ReviewProvider:
    if provider is not None:
        return provider
    config = load_config(get_config_path(home))
    return get_review_provider(config)


def preview_review(
    identifier: str,
    *,
    home: Path | None = None,
    provider: ReviewProvider | None = None,
) -> ReviewPreview:
    root = home or get_syca_home()
    critique_provider = _resolve_provider(root, provider)
    connection = open_initialized_database(get_database_path(root))
    try:
        node, node_file, mental_model, mental_model_hash = _load_review_context(
            connection, identifier, home=root
        )
        payload = build_review_payload(
            node_id=node.id,
            node_title=node.title,
            node_slug=node.slug,
            domain=node.domain,
            claimed_level=node.claimed_level.value,
            mental_model=mental_model,
            mental_model_hash=mental_model_hash,
        )
        return ReviewPreview(
            node=node,
            payload=payload,
            node_file=node_file,
            provider_name=critique_provider.name,
        )
    finally:
        connection.close()


def run_review(
    identifier: str,
    *,
    home: Path | None = None,
    provider: ReviewProvider | None = None,
) -> ReviewResult:
    root = home or get_syca_home()
    critique_provider = _resolve_provider(root, provider)
    preview = preview_review(identifier, home=root, provider=critique_provider)

    try:
        critique = critique_provider.critique(preview.payload)
    except RuntimeError as error:
        raise ReviewError(str(error)) from error
    reviews_dir = get_reviews_dir(root)
    reviews_dir.mkdir(parents=True, exist_ok=True)

    review_id = str(uuid.uuid4())
    raw_output_file = reviews_dir / f"{review_id}.json"
    raw_output_file.write_text(
        dumps_critique_raw(
            critique,
            preview.payload,
            provider_name=critique_provider.name,
        ),
        encoding="utf-8",
    )
    relative_raw_path = f"{REVIEWS_DIRNAME}/{raw_output_file.name}"

    connection = open_initialized_database(get_database_path(root))
    try:
        with connection:
            review_run = insert_review_run(
                connection,
                review_id=review_id,
                node_id=preview.node.id,
                mental_model_hash=preview.payload.mental_model_hash,
                prompt_version=PROMPT_VERSION,
                provider=critique_provider.name,
                critique=critique,
                raw_output_path=relative_raw_path,
            )
            update_review_status(connection, preview.node.id, ReviewStatus.CHALLENGED)
            connection.execute(
                """
                INSERT INTO capability_events (id, node_id, capture_id, type, payload_json, created_at)
                VALUES (?, ?, NULL, ?, ?, ?);
                """,
                (
                    str(uuid.uuid4()),
                    preview.node.id,
                    CapabilityEventType.REVIEW_COMPLETED.value,
                    json.dumps(
                        {
                            "reviewRunId": review_run.id,
                            "mentalModelHash": preview.payload.mental_model_hash,
                            "promptVersion": PROMPT_VERSION,
                            "provider": critique_provider.name,
                        },
                        ensure_ascii=False,
                    ),
                    utc_now_iso(),
                ),
            )
        updated_node = resolve_node_identifier(connection, preview.node.id)
        return ReviewResult(
            node=updated_node,
            review_run=review_run,
            raw_output_file=raw_output_file,
        )
    finally:
        connection.close()


def list_node_reviews(identifier: str, *, home: Path | None = None) -> list[ReviewRunSummary]:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        node, _, _, current_hash = _load_review_context(connection, identifier, home=root)
        reviews = list_reviews_for_node(connection, node.id)
        return [
            ReviewRunSummary(
                review=review,
                is_outdated=review.mental_model_hash != current_hash,
            )
            for review in reviews
        ]
    finally:
        connection.close()


def _review_status_for_decision(decision: UserDecision) -> ReviewStatus:
    if decision is UserDecision.ACCEPTED:
        return ReviewStatus.ACCEPTED_BY_USER
    if decision is UserDecision.REVISED:
        return ReviewStatus.NEEDS_REVISION
    return ReviewStatus.CHALLENGED


def decide_review(
    review_identifier: str,
    decision: UserDecision,
    *,
    home: Path | None = None,
) -> ReviewDecisionResult:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        try:
            review = resolve_review_identifier(connection, review_identifier)
        except ReviewRepositoryError as error:
            raise ReviewError(str(error)) from error

        with connection:
            updated_review = update_user_decision(connection, review.id, decision)
            update_review_status(
                connection,
                review.node_id,
                _review_status_for_decision(decision),
            )
        node = resolve_node_identifier(connection, review.node_id)
        return ReviewDecisionResult(review=updated_review, node=node)
    finally:
        connection.close()
