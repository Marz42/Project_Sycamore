"""Shared domain enumerations."""

from __future__ import annotations

from enum import StrEnum


class CaptureKind(StrEnum):
    NOTE = "note"
    CHEAT = "cheat"
    LINK = "link"
    SNIPPET = "snippet"
    QUESTION = "question"


class CaptureStatus(StrEnum):
    INBOX = "inbox"
    PROMOTED = "promoted"
    ARCHIVED = "archived"
    DISCARDED = "discarded"


class ClaimedLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


class ReviewStatus(StrEnum):
    NOT_REVIEWED = "not_reviewed"
    CHALLENGED = "challenged"
    NEEDS_REVISION = "needs_revision"
    ACCEPTED_BY_USER = "accepted_by_user"


class CapabilityEventType(StrEnum):
    CAPTURE_CREATED = "capture_created"
    CAPTURE_PROMOTED = "capture_promoted"
    PRACTICE_LOGGED = "practice_logged"
    CHEATSHEET_QUERIED = "cheatsheet_queried"
    REVIEW_COMPLETED = "review_completed"
    RECOVERY_PASSED = "recovery_passed"
    RECOVERY_FAILED = "recovery_failed"
    MANUAL_LEVEL_CHANGED = "manual_level_changed"
    NODE_SYNCED = "node_synced"
