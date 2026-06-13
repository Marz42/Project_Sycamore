"""Resolve and query ReviewRun records."""

from __future__ import annotations

import json
import sqlite3

from sycamore.models.enums import UserDecision
from sycamore.models.review_run import ReviewRun
from sycamore.review.provider import ReviewCritique
from sycamore.utils.time import utc_now_iso


class ReviewRepositoryError(Exception):
    """Raised when review persistence rules are violated."""


def _row_to_review(row: sqlite3.Row) -> ReviewRun:
    return ReviewRun(
        id=row["id"],
        node_id=row["node_id"],
        mental_model_hash=row["mental_model_hash"],
        prompt_version=row["prompt_version"],
        provider=row["provider"],
        summary=row["summary"],
        user_decision=UserDecision(row["user_decision"]),
        created_at=row["created_at"],
        model=row["model"],
        fact_issues_json=row["fact_issues_json"],
        boundary_issues_json=row["boundary_issues_json"],
        questions_json=row["questions_json"],
        practice_suggestions_json=row["practice_suggestions_json"],
        raw_output_path=row["raw_output_path"],
    )


def insert_review_run(
    connection: sqlite3.Connection,
    *,
    review_id: str,
    node_id: str,
    mental_model_hash: str,
    prompt_version: str,
    provider: str,
    critique: ReviewCritique,
    raw_output_path: str,
) -> ReviewRun:
    timestamp = utc_now_iso()
    connection.execute(
        """
        INSERT INTO review_runs (
            id, node_id, mental_model_hash, prompt_version, provider, model,
            summary, fact_issues_json, boundary_issues_json, questions_json,
            practice_suggestions_json, user_decision, raw_output_path, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            review_id,
            node_id,
            mental_model_hash,
            prompt_version,
            provider,
            critique.model,
            critique.summary,
            json.dumps(critique.fact_issues, ensure_ascii=False),
            json.dumps(critique.boundary_issues, ensure_ascii=False),
            json.dumps(critique.questions, ensure_ascii=False),
            json.dumps(critique.practice_suggestions, ensure_ascii=False),
            UserDecision.PENDING.value,
            raw_output_path,
            timestamp,
        ),
    )
    row = connection.execute(
        "SELECT * FROM review_runs WHERE id = ?;",
        (review_id,),
    ).fetchone()
    assert row is not None
    return _row_to_review(row)


def resolve_review_identifier(connection: sqlite3.Connection, identifier: str) -> ReviewRun:
    exact = get_review_by_id(connection, identifier)
    if exact is not None:
        return exact

    prefix_matches = connection.execute(
        "SELECT * FROM review_runs WHERE id LIKE ? ORDER BY created_at DESC;",
        (f"{identifier}%",),
    ).fetchall()
    if len(prefix_matches) == 1:
        return _row_to_review(prefix_matches[0])
    if len(prefix_matches) > 1:
        raise ReviewRepositoryError(
            f"Review identifier '{identifier}' matches multiple runs. Use a longer prefix."
        )
    raise ReviewRepositoryError(f"Review not found: {identifier}")


def get_review_by_id(connection: sqlite3.Connection, review_id: str) -> ReviewRun | None:
    row = connection.execute(
        "SELECT * FROM review_runs WHERE id = ?;",
        (review_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_review(row)


def list_reviews_for_node(connection: sqlite3.Connection, node_id: str) -> list[ReviewRun]:
    rows = connection.execute(
        """
        SELECT * FROM review_runs
        WHERE node_id = ?
        ORDER BY created_at DESC;
        """,
        (node_id,),
    ).fetchall()
    return [_row_to_review(row) for row in rows]


def update_user_decision(
    connection: sqlite3.Connection,
    review_id: str,
    decision: UserDecision,
) -> ReviewRun:
    updated = connection.execute(
        """
        UPDATE review_runs
        SET user_decision = ?
        WHERE id = ?;
        """,
        (decision.value, review_id),
    ).rowcount
    if updated != 1:
        raise ReviewRepositoryError(f"Review not found: {review_id}")

    row = connection.execute(
        "SELECT * FROM review_runs WHERE id = ?;",
        (review_id,),
    ).fetchone()
    assert row is not None
    return _row_to_review(row)
