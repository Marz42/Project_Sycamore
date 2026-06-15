"""SQLite schema definitions for Sycamore."""

SCHEMA_VERSION = 3

SCHEMA_STATEMENTS: tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ability_nodes (
        id TEXT PRIMARY KEY,
        slug TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        domain TEXT,
        node_type TEXT NOT NULL DEFAULT 'capability' CHECK (
            node_type IN ('capability', 'concept', 'theorem', 'process')
        ),
        claimed_level TEXT NOT NULL CHECK (claimed_level IN ('L0', 'L1', 'L2', 'L3')),
        review_status TEXT NOT NULL CHECK (
            review_status IN ('not_reviewed', 'challenged', 'needs_revision', 'accepted_by_user')
        ),
        node_path TEXT NOT NULL UNIQUE,
        content_hash TEXT NOT NULL,
        front_matter_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_synced_at TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS capture_items (
        id TEXT PRIMARY KEY,
        kind TEXT NOT NULL CHECK (kind IN ('note', 'cheat', 'link', 'snippet', 'question')),
        content TEXT NOT NULL,
        context TEXT,
        source TEXT,
        status TEXT NOT NULL CHECK (status IN ('inbox', 'promoted', 'archived', 'discarded')),
        promoted_node_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (promoted_node_id) REFERENCES ability_nodes(id)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS capability_events (
        id TEXT PRIMARY KEY,
        node_id TEXT,
        capture_id TEXT,
        type TEXT NOT NULL CHECK (
            type IN (
                'capture_created',
                'capture_promoted',
                'practice_logged',
                'cheatsheet_queried',
                'review_completed',
                'recovery_passed',
                'recovery_failed',
                'manual_level_changed',
                'node_synced'
            )
        ),
        payload_json TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (node_id) REFERENCES ability_nodes(id) ON DELETE CASCADE,
        FOREIGN KEY (capture_id) REFERENCES capture_items(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS ability_edges (
        id TEXT PRIMARY KEY,
        source_node_id TEXT NOT NULL,
        target_node_id TEXT NOT NULL,
        type TEXT NOT NULL CHECK (
            type IN ('prerequisite', 'related', 'similar_pattern', 'contrasts_with', 'used_in_scenario')
        ),
        confidence TEXT NOT NULL CHECK (confidence IN ('explicit', 'implicit', 'suggested', 'derived')),
        rationale TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (source_node_id) REFERENCES ability_nodes(id) ON DELETE CASCADE,
        FOREIGN KEY (target_node_id) REFERENCES ability_nodes(id) ON DELETE CASCADE,
        UNIQUE (source_node_id, target_node_id, type)
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS review_runs (
        id TEXT PRIMARY KEY,
        node_id TEXT NOT NULL,
        mental_model_hash TEXT NOT NULL,
        prompt_version TEXT NOT NULL,
        provider TEXT NOT NULL,
        model TEXT,
        summary TEXT NOT NULL,
        fact_issues_json TEXT,
        boundary_issues_json TEXT,
        questions_json TEXT,
        practice_suggestions_json TEXT,
        user_decision TEXT NOT NULL CHECK (user_decision IN ('pending', 'accepted', 'ignored', 'revised')),
        raw_output_path TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (node_id) REFERENCES ability_nodes(id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS node_scheduler_state (
        node_id TEXT PRIMARY KEY,
        stability REAL NOT NULL DEFAULT 0,
        difficulty REAL NOT NULL DEFAULT 5.0,
        due_at TEXT,
        last_review_at TEXT,
        last_rating INTEGER,
        review_count INTEGER DEFAULT 0,
        lapse_count INTEGER DEFAULT 0,
        FOREIGN KEY (node_id) REFERENCES ability_nodes(id) ON DELETE CASCADE
    );
    """,
)
