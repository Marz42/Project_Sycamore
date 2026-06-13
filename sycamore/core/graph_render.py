"""Render domain graphs as terminal-friendly text."""

from __future__ import annotations

from collections import defaultdict

from sycamore.core.graph_service import DomainGraph
from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import EdgeType


def _node_label(node: AbilityNode) -> str:
    return f"{node.title} ({node.slug})"


def _render_prerequisite_tree(
    *,
    roots: list[str],
    children_map: dict[str, list[str]],
    node_by_id: dict[str, AbilityNode],
    visited: set[str],
    lines: list[str],
) -> None:
    def walk(node_id: str, prefix: str, is_last: bool, is_root: bool) -> None:
        if node_id in visited:
            connector = "" if is_root else ("└── " if is_last else "├── ")
            lines.append(f"{prefix}{connector}{_node_label(node_by_id[node_id])} [cycle]")
            return

        visited.add(node_id)
        if is_root:
            lines.append(_node_label(node_by_id[node_id]))
        else:
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{_node_label(node_by_id[node_id])}")

        children = children_map.get(node_id, [])
        child_prefix = prefix if is_root else prefix + ("    " if is_last else "│   ")
        for index, child_id in enumerate(children):
            walk(child_id, child_prefix, index == len(children) - 1, is_root=False)

    for index, root_id in enumerate(roots):
        if index > 0:
            lines.append("")
        walk(root_id, "", True, is_root=True)


def format_domain_graph_text(domain_graph: DomainGraph) -> list[str]:
    """Build multi-section ASCII graph lines for a domain."""
    node_by_id = {node.id: node for node in domain_graph.nodes}
    lines: list[str] = [
        f"Domain: {domain_graph.domain} ({len(domain_graph.nodes)} nodes, {len(domain_graph.edges)} links)",
        "",
    ]

    if not domain_graph.edges:
        lines.append("No links yet. Unlinked nodes:")
        for node in sorted(domain_graph.nodes, key=lambda item: item.title.lower()):
            lines.append(f"  • {_node_label(node)}")
        return lines

    edges_by_type: dict[EdgeType, list] = defaultdict(list)
    for edge in domain_graph.edges:
        edges_by_type[edge.edge_type].append(edge)

    connected_ids: set[str] = set()
    for edge in domain_graph.edges:
        connected_ids.add(edge.source_node_id)
        connected_ids.add(edge.target_node_id)

    visited: set[str] = set()

    for edge_type in EdgeType:
        edges = edges_by_type.get(edge_type)
        if not edges:
            continue

        lines.append(f"[{edge_type.value}]")

        if edge_type is EdgeType.PREREQUISITE:
            children_map: dict[str, list[str]] = defaultdict(list)
            targets: set[str] = set()
            for edge in edges:
                children_map[edge.source_node_id].append(edge.target_node_id)
                targets.add(edge.target_node_id)

            roots = sorted(
                (node_id for node_id in children_map if node_id not in targets),
                key=lambda node_id: node_by_id[node_id].title.lower(),
            )
            if roots:
                _render_prerequisite_tree(
                    roots=roots,
                    children_map=children_map,
                    node_by_id=node_by_id,
                    visited=visited,
                    lines=lines,
                )

            orphan_sources = sorted(
                (
                    node_id
                    for node_id in children_map
                    if node_id not in roots and node_id not in visited
                ),
                key=lambda node_id: node_by_id[node_id].title.lower(),
            )
            for node_id in orphan_sources:
                if lines and lines[-1] != "":
                    lines.append("")
                _render_prerequisite_tree(
                    roots=[node_id],
                    children_map=children_map,
                    node_by_id=node_by_id,
                    visited=visited,
                    lines=lines,
                )
        else:
            for edge in sorted(
                edges,
                key=lambda item: (
                    node_by_id[item.source_node_id].title.lower(),
                    node_by_id[item.target_node_id].title.lower(),
                ),
            ):
                source = node_by_id[edge.source_node_id]
                target = node_by_id[edge.target_node_id]
                arrow = f"──{edge.edge_type.value}──>"
                if edge.rationale:
                    lines.append(f"  {source.title} {arrow} {target.title}")
                    lines.append(f"      ↳ {edge.rationale}")
                else:
                    lines.append(f"  {source.title} {arrow} {target.title}")
                visited.add(edge.source_node_id)
                visited.add(edge.target_node_id)

        lines.append("")

    truly_unlinked = [
        node for node in domain_graph.nodes if node.id not in connected_ids
    ]
    if truly_unlinked:
        lines.append("[unlinked]")
        for node in sorted(truly_unlinked, key=lambda item: item.title.lower()):
            lines.append(f"  • {_node_label(node)}")
        lines.append("")

    if lines and lines[-1] == "":
        lines.pop()

    return lines
