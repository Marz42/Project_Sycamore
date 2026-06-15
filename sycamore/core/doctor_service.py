"""Check local Markdown and SQLite consistency."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sycamore.storage.database import open_initialized_database
from sycamore.storage.markdown_parser import parse_node_markdown
from sycamore.storage.node_repository import list_all_nodes
from sycamore.models.enums import NodeType
from sycamore.utils.paths import NODES_DIRNAME, get_database_path, get_nodes_dir, get_syca_home


@dataclass(frozen=True)
class DoctorIssue:
    code: str
    message: str
    path: str | None = None


@dataclass(frozen=True)
class DoctorReport:
    issues: tuple[DoctorIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


def run_doctor(*, home: Path | None = None) -> DoctorReport:
    root = home or get_syca_home()
    nodes_dir = get_nodes_dir(root)
    issues: list[DoctorIssue] = []

    connection = open_initialized_database(get_database_path(root))
    try:
        indexed_nodes = list_all_nodes(connection)
        indexed_ids = {node.id for node in indexed_nodes}
        indexed_paths = {node.node_path for node in indexed_nodes}

        for node in indexed_nodes:
            node_file = root / node.node_path
            if not node_file.exists():
                issues.append(
                    DoctorIssue(
                        code="missing_markdown",
                        message=f"Indexed node {node.id} points to missing file.",
                        path=node.node_path,
                    )
                )
                continue

            parsed = parse_node_markdown(node_file)
            if parsed.missing_fields:
                issues.append(
                    DoctorIssue(
                        code="missing_front_matter",
                        message=(
                            f"Markdown {node.node_path} is missing required fields: "
                            f"{', '.join(parsed.missing_fields)}"
                        ),
                        path=node.node_path,
                    )
                )
                continue

            if parsed.node_id != node.id:
                issues.append(
                    DoctorIssue(
                        code="id_mismatch",
                        message=(
                            f"Front matter id {parsed.node_id} does not match index id {node.id}."
                        ),
                        path=node.node_path,
                    )
                )
            if parsed.content_hash != node.content_hash:
                issues.append(
                    DoctorIssue(
                        code="content_hash_mismatch",
                        message=f"Content hash mismatch for {node.node_path}. Run `syca sync`.",
                        path=node.node_path,
                    )
                )
            if parsed.front_matter_hash != node.front_matter_hash:
                issues.append(
                    DoctorIssue(
                        code="front_matter_hash_mismatch",
                        message=(
                            f"Front matter hash mismatch for {node.node_path}. Run `syca sync`."
                        ),
                        path=node.node_path,
                    )
                )

            valid_types = {t.value for t in NodeType}
            if parsed.node_type not in valid_types:
                issues.append(
                    DoctorIssue(
                        code="invalid_node_type",
                        message=(
                            f"Invalid node_type '{parsed.node_type}' in {node.node_path}. "
                            f"Expected one of: {', '.join(sorted(valid_types))}. "
                            f"Run `syca sync` to default to 'capability'."
                        ),
                        path=node.node_path,
                    )
                )

        slug_to_paths: dict[str, list[str]] = {}
        seen_ids: dict[str, str] = {}

        if nodes_dir.exists():
            for markdown_path in sorted(nodes_dir.glob("*.md")):
                relative_path = f"{NODES_DIRNAME}/{markdown_path.name}"
                parsed = parse_node_markdown(markdown_path)

                if parsed.missing_fields:
                    if relative_path not in indexed_paths:
                        issues.append(
                            DoctorIssue(
                                code="orphan_markdown",
                                message=(
                                    f"Orphan Markdown {relative_path} is missing required fields: "
                                    f"{', '.join(parsed.missing_fields)}"
                                ),
                                path=relative_path,
                            )
                        )
                    continue

                if parsed.node_id not in indexed_ids:
                    issues.append(
                        DoctorIssue(
                            code="orphan_markdown",
                            message=f"Markdown {relative_path} is not indexed in SQLite.",
                            path=relative_path,
                        )
                    )

                if parsed.node_id in seen_ids and seen_ids[parsed.node_id] != relative_path:
                    issues.append(
                        DoctorIssue(
                            code="duplicate_node_id",
                            message=(
                                f"Duplicate node id {parsed.node_id} in "
                                f"{seen_ids[parsed.node_id]} and {relative_path}."
                            ),
                            path=relative_path,
                        )
                    )
                seen_ids[parsed.node_id] = relative_path
                slug_to_paths.setdefault(parsed.slug, []).append(relative_path)

        for slug, paths in slug_to_paths.items():
            if len(paths) > 1:
                issues.append(
                    DoctorIssue(
                        code="slug_conflict",
                        message=f"Slug '{slug}' is used by multiple files: {', '.join(paths)}.",
                        path=paths[0],
                    )
                )

        edge_rows = connection.execute(
            "SELECT id, source_node_id, target_node_id FROM ability_edges;"
        ).fetchall()
        for row in edge_rows:
            for node_id in (row["source_node_id"], row["target_node_id"]):
                if node_id not in indexed_ids:
                    issues.append(
                        DoctorIssue(
                            code="invalid_edge",
                            message=(
                                f"Edge {row['id']} references missing node {node_id}."
                            ),
                        )
                    )
    finally:
        connection.close()

    return DoctorReport(issues=tuple(issues))
