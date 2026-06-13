"""Domain graph views."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sycamore.models.ability_edge import AbilityEdge
from sycamore.models.ability_node import AbilityNode
from sycamore.storage.database import open_initialized_database
from sycamore.storage.edge_repository import list_edges_for_domain
from sycamore.storage.node_repository import list_nodes_by_domain
from sycamore.utils.paths import get_database_path, get_syca_home


class GraphError(Exception):
    """Raised when graph cannot be built."""


@dataclass(frozen=True)
class DomainGraph:
    domain: str
    nodes: tuple[AbilityNode, ...]
    edges: tuple[AbilityEdge, ...]


def build_domain_graph(domain: str, *, home: Path | None = None) -> DomainGraph:
    root = home or get_syca_home()
    connection = open_initialized_database(get_database_path(root))
    try:
        nodes = list_nodes_by_domain(connection, domain)
        if not nodes:
            raise GraphError(f"No nodes found in domain '{domain}'.")
        edges = list_edges_for_domain(connection, domain)
        return DomainGraph(domain=domain, nodes=tuple(nodes), edges=tuple(edges))
    finally:
        connection.close()
