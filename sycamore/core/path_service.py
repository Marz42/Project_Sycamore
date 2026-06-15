"""Path view and graph analysis — Phase 4."""

from __future__ import annotations

from dataclasses import dataclass

from sycamore.models.ability_node import AbilityNode
from sycamore.models.enums import EdgeType
from sycamore.storage.database import open_initialized_database
from sycamore.storage.node_repository import list_nodes_by_domain
from sycamore.utils.paths import get_database_path, get_syca_home
from pathlib import Path


class PathError(Exception):
    """Raised when path analysis fails."""


@dataclass(frozen=True)
class PathChain:
    """A single prerequisite + composition chain."""
    nodes: tuple[AbilityNode, ...]
    edges: tuple[tuple[str, str, str], ...]  # (from_slug, to_slug, edge_type)


@dataclass(frozen=True)
class PathReport:
    domain: str
    chains: tuple[PathChain, ...]
    unlinked: tuple[AbilityNode, ...]


def _get_edges(connection, domain_nodes: list[AbilityNode]) -> list[tuple[str, str, str, str]]:
    """Return (source_id, target_id, type, rationale) for edges within domain."""
    node_ids = {n.id for n in domain_nodes}
    rows = connection.execute(
        """
        SELECT source_node_id, target_node_id, type, rationale
        FROM ability_edges
        WHERE source_node_id IN ({0}) AND target_node_id IN ({0});
        """.format(",".join("?" * len(node_ids))),
        tuple(node_ids) + tuple(node_ids),
    ).fetchall()
    return [(r["source_node_id"], r["target_node_id"], r["type"], r["rationale"] or "") for r in rows]


def _build_chains(
    nodes: list[AbilityNode],
    edges: list[tuple[str, str, str, str]],
    edge_types: tuple[str, ...],
) -> list[PathChain]:
    """Build chains using only specified edge types."""
    id_to_node = {n.id: n for n in nodes}
    adj: dict[str, list[tuple[str, str]]] = {}  # source → [(target, type)]
    for src, tgt, typ, _ in edges:
        if typ in edge_types:
            adj.setdefault(src, []).append((tgt, typ))

    in_degree: dict[str, int] = {n.id: 0 for n in nodes}
    for src, tgt, typ, _ in edges:
        if typ in edge_types:
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

    visited: set[str] = set()
    chains: list[PathChain] = []

    # Start from nodes with no incoming edges (roots)
    for node in nodes:
        if in_degree.get(node.id, 0) == 0 and node.id not in visited:
            chain_nodes: list[AbilityNode] = [node]
            chain_edges: list[tuple[str, str, str]] = []
            current = node.id
            visited.add(current)

            while current in adj:
                # Take first outgoing edge
                tgt, typ = adj[current][0]
                if tgt in visited:
                    break
                chain_nodes.append(id_to_node[tgt])
                chain_edges.append((id_to_node[current].slug, id_to_node[tgt].slug, typ))
                visited.add(tgt)
                current = tgt

            if len(chain_nodes) > 1:
                chains.append(PathChain(
                    nodes=tuple(chain_nodes),
                    edges=tuple(chain_edges),
                ))

    # Remaining nodes not in any chain
    return chains


def build_path_report(
    domain: str,
    *,
    home: Path | None = None,
) -> PathReport:
    """Build prerequisite + composition path chains for a domain."""
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        nodes = list_nodes_by_domain(connection, domain)
        if not nodes:
            raise PathError(f"No nodes found in domain '{domain}'.")

        edges = _get_edges(connection, nodes)
        chains = _build_chains(
            nodes, edges,
            (EdgeType.PREREQUISITE.value, EdgeType.COMPOSITION.value),
        )

        chained_ids: set[str] = set()
        for chain in chains:
            for node in chain.nodes:
                chained_ids.add(node.id)

        unlinked = tuple(n for n in nodes if n.id not in chained_ids)
        return PathReport(domain=domain, chains=tuple(chains), unlinked=unlinked)
    finally:
        connection.close()
