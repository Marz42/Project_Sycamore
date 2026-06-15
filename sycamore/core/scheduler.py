"""FSRS-5 scheduler — spaced repetition algorithm (Anki-compatible defaults)."""

from __future__ import annotations

import math
from dataclasses import dataclass

# ── FSRS-5 default weights (w0..w16) ────────────────────────────────
# Source: Anki FSRS-5 defaults (2024)
_W: list[float] = [
    0.40255,   # w0
    1.18385,   # w1
    3.173,     # w2
    15.69105,  # w3
    7.1949,    # w4
    0.5345,    # w5
    1.4604,    # w6
    0.0046,    # w7
    1.54575,   # w8
    0.1192,    # w9
    1.01925,   # w10
    1.9395,    # w11
    0.11,      # w12
    0.29605,   # w13
    2.2698,    # w14
    0.2315,    # w15
    2.9898,    # w16
]

DEFAULT_DESIRED_RETENTION = 0.9
DEFAULT_MAX_PER_SESSION = 20

_RATING_VALUES: dict[str, int] = {"fail": 1, "hard": 2, "pass": 3, "easy": 4}


def rating_to_int(rating: str) -> int:
    """Map recover rating string to FSRS integer (1-4)."""
    return _RATING_VALUES[rating]


# ── Core FSRS-5 formulas ────────────────────────────────────────────


def _R(t: float, S: float) -> float:
    """Retrievability: probability of recall after t days with stability S."""
    return (1.0 + 19.0 * t / max(S, 0.01)) ** -1.0


def _S0(G: int) -> float:
    """Initial stability after first rating G (1-4)."""
    return _W[G - 1]


def _D0(G: int) -> float:
    """Initial difficulty after first rating G."""
    return _W[4] - (G - 3) * _W[5]


def _next_D(G: int, D: float) -> float:
    """Update difficulty after rating G."""
    if G == 1:
        delta = -_W[5]
    elif G == 2:
        delta = -_W[5] / 3.0
    elif G == 3:
        delta = 0.0
    else:  # G == 4
        delta = _W[5]
    D_prime = D + delta
    # Mean reversion toward w4
    D_prime = _W[4] + (D_prime - _W[4]) * _W[15]
    return max(1.0, min(10.0, D_prime))


def _next_S(G: int, D: float, S: float, R_val: float) -> float:
    """Post-review stability."""
    if G == 1:  # Again → post-lapse stability
        S_prime = (
            _W[6]
            * (D**_W[7])
            * ((S + 1.0) ** _W[8] - 1.0)
            * math.exp(_W[9] * (1.0 - R_val))
        )
        return min(S_prime, S)

    # Hard (2), Good (3), Easy (4)
    S_prime = S * (
        1.0
        + math.exp(_W[10])
        * (11.0 - D)
        * (S**_W[11])
        * (math.exp(_W[12] * (1.0 - R_val)) - 1.0)
    )
    if G == 2:  # Hard penalty
        S_prime *= _W[13]
    elif G == 4:  # Easy bonus
        S_prime *= _W[14]
    return min(S_prime, 36500.0)  # cap at ~100 years


def _next_interval(S: float, desired_retention: float) -> int:
    """Days until retrievability drops to desired retention."""
    # FSRS interval formula: factor = 9 (standard Anki)
    days = S * 9.0 * (1.0 / desired_retention - 1.0)
    return max(1, min(round(days), 36500))  # cap at ~100 years


# ── Public API ───────────────────────────────────────────────────────


@dataclass(frozen=True)
class SchedulerState:
    node_id: str
    stability: float
    difficulty: float
    due_at: str | None
    last_review_at: str | None
    last_rating: int | None
    review_count: int
    lapse_count: int


def init_state(
    rating: str,
    *,
    now_iso: str,
) -> SchedulerState:
    """Create initial FSRS state from the first recover rating."""
    G = rating_to_int(rating)
    S = _S0(G)
    D = _D0(G)
    days = _next_interval(S, DEFAULT_DESIRED_RETENTION)
    # due_at = now + interval days (simple ISO concatenation for now)
    due_at = _add_days(now_iso, days)
    return SchedulerState(
        node_id="",  # caller fills in
        stability=S,
        difficulty=D,
        due_at=due_at,
        last_review_at=now_iso,
        last_rating=G,
        review_count=1,
        lapse_count=1 if G == 1 else 0,
    )


def update_state(
    state: SchedulerState,
    rating: str,
    *,
    now_iso: str,
    desired_retention: float = DEFAULT_DESIRED_RETENTION,
) -> SchedulerState:
    """Update FSRS state after a review rating."""
    G = rating_to_int(rating)
    D = _next_D(G, state.difficulty)
    # Calculate current retrievability
    days_since = _days_between(state.last_review_at or now_iso, now_iso)
    R_val = _R(days_since, state.stability)
    S = _next_S(G, D if G != 1 else state.difficulty, state.stability, R_val)
    # For again (G=1): use new difficulty for interval calc
    days = _next_interval(S, desired_retention)
    due_at = _add_days(now_iso, days)

    return SchedulerState(
        node_id=state.node_id,
        stability=S,
        difficulty=D,
        due_at=due_at,
        last_review_at=now_iso,
        last_rating=G,
        review_count=state.review_count + 1,
        lapse_count=state.lapse_count + (1 if G == 1 else 0),
    )


def current_retrievability(state: SchedulerState, now_iso: str) -> float:
    """Compute current R (0-1) for a node."""
    if state.last_review_at is None:
        return 1.0
    days = _days_between(state.last_review_at, now_iso)
    return _R(days, max(state.stability, 0.01))


# ── Helpers ──────────────────────────────────────────────────────────


def _add_days(iso: str, days: int) -> str:
    """Simple ISO date arithmetic (assumes UTC format)."""
    from datetime import datetime, timedelta
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (dt + timedelta(days=days)).isoformat()


def _days_between(earlier_iso: str, later_iso: str) -> float:
    from datetime import datetime
    earlier = datetime.fromisoformat(earlier_iso.replace("Z", "+00:00"))
    later = datetime.fromisoformat(later_iso.replace("Z", "+00:00"))
    return (later - earlier).total_seconds() / 86400.0
