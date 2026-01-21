"""Query helpers for PatternedGraph program graphs."""

from __future__ import annotations

from dataclasses import dataclass

from .graph import EndpointId, InstId, ModuleId, NetId, ProgramGraph
from .index import GraphIndex


@dataclass(frozen=True)
class DesignQuery:
    """Derived query helpers for a program graph.

    Attributes:
        graph: Source ProgramGraph for the query helpers.
        module_indexes: Per-module GraphIndex instances.
    """

    graph: ProgramGraph
    module_indexes: dict[ModuleId, GraphIndex]

    @classmethod
    def from_program(cls, graph: ProgramGraph) -> DesignQuery:
        """Build DesignQuery helpers from a program graph.

        Args:
            graph: ProgramGraph to index.

        Returns:
            DesignQuery helper with per-module indices.
        """
        module_indexes = {
            module_id: GraphIndex.from_module(module, graph.registries)
            for module_id, module in graph.modules.items()
        }
        return cls(graph=graph, module_indexes=module_indexes)

    def net_id(self, module_id: ModuleId, name: str) -> NetId | None:
        """Resolve a net name to its ID within a module.

        Args:
            module_id: Module identifier to query.
            name: Raw net name expression.

        Returns:
            NetId if found, otherwise None.
        """
        return self.module_indexes[module_id].net_name_to_id.get(name)

    def inst_id(self, module_id: ModuleId, name: str) -> InstId | None:
        """Resolve an instance name to its ID within a module.

        Args:
            module_id: Module identifier to query.
            name: Raw instance name expression.

        Returns:
            InstId if found, otherwise None.
        """
        return self.module_indexes[module_id].inst_name_to_id.get(name)

    def net_endpoints(self, module_id: ModuleId, net_id: NetId) -> list[EndpointId]:
        """Return the ordered endpoints for a net.

        Args:
            module_id: Module identifier to query.
            net_id: Net identifier.

        Returns:
            Ordered list of endpoint IDs (empty if missing).
        """
        endpoints = self.module_indexes[module_id].net_to_endpoints.get(net_id)
        if endpoints is None:
            return []
        return list(endpoints)

    def net_endpoints_by_name(
        self, module_id: ModuleId, net_name: str
    ) -> list[EndpointId]:
        """Return the ordered endpoints for a net by name.

        Args:
            module_id: Module identifier to query.
            net_name: Raw net name expression.

        Returns:
            Ordered list of endpoint IDs (empty if missing).
        """
        net_id = self.net_id(module_id, net_name)
        if net_id is None:
            return []
        return self.net_endpoints(module_id, net_id)


def query(graph: ProgramGraph) -> DesignQuery:
    """Construct a DesignQuery helper from a ProgramGraph.

    Args:
        graph: ProgramGraph to query.

    Returns:
        DesignQuery instance for the graph.
    """
    return DesignQuery.from_program(graph)


__all__ = ["DesignQuery", "query"]
