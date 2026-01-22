"""Atomic builder helpers for PatternedGraph creation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional

from asdl.diagnostics import SourceSpan

from .graph import EndpointBundle, InstanceBundle, ModuleGraph, NetBundle, ProgramGraph
from .registries import (
    AnnotationIndex,
    ExprId,
    GraphId,
    GroupSlice,
    ParamPatternOriginIndex,
    PatternExpr,
    PatternExpressionRegistry,
    PatternOriginIndex,
    RegistrySet,
    SchematicHints,
    SourceSpanIndex,
)


@dataclass
class _IdAllocator:
    """Deterministic ID allocator for PatternedGraph entities."""

    _counts: Dict[str, int]

    def __init__(self) -> None:
        self._counts = {}

    def next(self, prefix: str) -> str:
        """Return the next identifier for a prefix.

        Args:
            prefix: Prefix to namespace the identifier.

        Returns:
            A stable identifier string.
        """
        count = self._counts.get(prefix, 0) + 1
        self._counts[prefix] = count
        return f"{prefix}{count}"


class PatternedGraphBuilder:
    """Build PatternedGraph programs via atomic operations."""

    def __init__(self) -> None:
        self._id_allocator = _IdAllocator()
        self._modules: Dict[str, ModuleGraph] = {}
        self._pattern_expressions: PatternExpressionRegistry = {}
        self._pattern_origins: PatternOriginIndex = {}
        self._param_pattern_origins: ParamPatternOriginIndex = {}
        self._source_spans: SourceSpanIndex = {}
        self._net_groups: Dict[GraphId, list[GroupSlice]] = {}
        self._annotations: AnnotationIndex = {}

    def add_module(self, name: str, file_id: str) -> ModuleGraph:
        """Create a module graph and register it in the program.

        Args:
            name: Module name.
            file_id: Source file identifier.

        Returns:
            Newly created ModuleGraph instance.
        """
        module_id = self._id_allocator.next("m")
        module = ModuleGraph(module_id=module_id, name=name, file_id=file_id)
        self._modules[module_id] = module
        return module

    def add_net(self, module_id: str, name_expr_id: ExprId) -> str:
        """Create a net bundle in the specified module.

        Args:
            module_id: Owning module identifier.
            name_expr_id: Expression ID for the net name.

        Returns:
            Net identifier string.

        Raises:
            KeyError: If the module does not exist.
        """
        module = self._modules[module_id]
        net_id = self._id_allocator.next("n")
        module.nets[net_id] = NetBundle(
            net_id=net_id,
            name_expr_id=name_expr_id,
            endpoint_ids=[],
        )
        return net_id

    def add_instance(
        self,
        module_id: str,
        name_expr_id: ExprId,
        ref_kind: Literal["module", "device"],
        ref_id: GraphId,
        ref_raw: str,
        *,
        param_expr_ids: Optional[Dict[str, ExprId]] = None,
    ) -> str:
        """Create an instance bundle in the specified module.

        Args:
            module_id: Owning module identifier.
            name_expr_id: Expression ID for the instance name.
            ref_kind: Reference kind (module or device).
            ref_id: Reference identifier.
            ref_raw: Raw reference token.
            param_expr_ids: Optional parameter expression mapping.

        Returns:
            Instance identifier string.

        Raises:
            KeyError: If the module does not exist.
        """
        module = self._modules[module_id]
        inst_id = self._id_allocator.next("i")
        module.instances[inst_id] = InstanceBundle(
            inst_id=inst_id,
            name_expr_id=name_expr_id,
            ref_kind=ref_kind,
            ref_id=ref_id,
            ref_raw=ref_raw,
            param_expr_ids=param_expr_ids or None,
        )
        return inst_id

    def add_endpoint(self, module_id: str, net_id: str, port_expr_id: ExprId) -> str:
        """Create an endpoint bundle and attach it to a net.

        Args:
            module_id: Owning module identifier.
            net_id: Net identifier owning the endpoint.
            port_expr_id: Expression ID for the endpoint token.

        Returns:
            Endpoint identifier string.

        Raises:
            KeyError: If the module or net does not exist.
        """
        module = self._modules[module_id]
        net = module.nets[net_id]
        endpoint_id = self._id_allocator.next("e")
        module.endpoints[endpoint_id] = EndpointBundle(
            endpoint_id=endpoint_id,
            net_id=net_id,
            port_expr_id=port_expr_id,
        )
        net.endpoint_ids.append(endpoint_id)
        return endpoint_id

    def add_expression(self, expression: PatternExpr) -> ExprId:
        """Register a parsed pattern expression.

        Args:
            expression: Parsed pattern expression object.

        Returns:
            Expression identifier string.
        """
        expr_id = f"expr{len(self._pattern_expressions) + 1}"
        self._pattern_expressions[expr_id] = expression
        return expr_id

    def register_pattern_origin(
        self,
        entity_id: GraphId,
        expr_id: ExprId,
        segment_index: int = 0,
        token_index: int = 0,
    ) -> None:
        """Record a pattern origin tuple for a graph entity.

        Args:
            entity_id: Graph entity identifier.
            expr_id: Expression identifier.
            segment_index: Index of the originating segment.
            token_index: Index of the originating token.
        """
        self._pattern_origins[entity_id] = (expr_id, segment_index, token_index)

    def register_param_origin(
        self, inst_id: GraphId, param_name: str, expr_id: ExprId, token_index: int = 0
    ) -> None:
        """Record a pattern origin tuple for an instance parameter.

        Args:
            inst_id: Instance identifier.
            param_name: Parameter name.
            expr_id: Expression identifier.
            token_index: Index of the originating token.
        """
        self._param_pattern_origins[(inst_id, param_name)] = (expr_id, token_index)

    def register_source_span(self, entity_id: GraphId, span: SourceSpan) -> None:
        """Record a source span for a graph entity.

        Args:
            entity_id: Graph entity identifier.
            span: Source span to store.
        """
        self._source_spans[entity_id] = span

    def register_net_groups(self, net_id: GraphId, group_slices: list[GroupSlice]) -> None:
        """Record grouped endpoint slices for schematic hints.

        Args:
            net_id: Net identifier.
            group_slices: Group slices to store.
        """
        if group_slices:
            self._net_groups[net_id] = group_slices

    def add_annotation(self, entity_id: GraphId, payload: Dict[str, object]) -> None:
        """Attach annotation metadata to a graph entity.

        Args:
            entity_id: Graph entity identifier.
            payload: Annotation payload to attach.
        """
        self._annotations[entity_id] = payload

    def set_port_order(self, module_id: str, port_order: Optional[list[str]]) -> None:
        """Update the port order for a module graph.

        Args:
            module_id: Module identifier to update.
            port_order: Ordered list of ports or None.

        Raises:
            KeyError: If the module does not exist.
        """
        module = self._modules[module_id]
        module.port_order = port_order or None

    def build(self) -> ProgramGraph:
        """Finalize and return a ProgramGraph with optional registries.

        Returns:
            ProgramGraph instance built from registered entities.
        """
        registries = RegistrySet(
            pattern_expressions=self._pattern_expressions or None,
            pattern_origins=self._pattern_origins or None,
            param_pattern_origins=self._param_pattern_origins or None,
            source_spans=self._source_spans or None,
            schematic_hints=(
                SchematicHints(net_groups=self._net_groups) if self._net_groups else None
            ),
            annotations=self._annotations or None,
        )
        return ProgramGraph(modules=self._modules, registries=registries)


__all__ = ["PatternedGraphBuilder"]
