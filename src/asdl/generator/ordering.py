from __future__ import annotations

from typing import Dict, List, Optional, Set

from ..data_structures import ASDLFile, Module


def _is_hierarchical(module: Module) -> bool:
    return module.instances is not None


def _build_adjacency(asdl_file: ASDLFile) -> Dict[str, List[str]]:
    """Build parent -> hierarchical children adjacency using deterministic ordering.

    - Only considers hierarchical modules as nodes
    - Edges only to hierarchical children (primitives are leaves and not nodes)
    - Preserves insertion order of modules and instances for determinism
    """
    adjacency: Dict[str, List[str]] = {}
    for module_name, module in asdl_file.modules.items():
        if not _is_hierarchical(module):
            continue
        children: List[str] = []
        if module.instances:
            for _inst_id, inst in module.instances.items():
                if inst.model in asdl_file.modules and _is_hierarchical(asdl_file.modules[inst.model]):
                    children.append(inst.model)
        adjacency[module_name] = children
    return adjacency


def compute_hierarchical_dependency_order(
    asdl_file: ASDLFile, top_module: Optional[str]
) -> List[str]:
    """Return hierarchical modules in children-first order with top last.

    - If top_module is provided and hierarchical, emit its reachable subgraph first (excluding top),
      then any orphan hierarchical groups, and finally the top itself as the last item.
    - Otherwise, emit all hierarchical groups in deterministic children-first order.
    - Cycle safety: back-edges are ignored to finish traversal deterministically.
    """
    adjacency = _build_adjacency(asdl_file)
    hierarchical_modules: Set[str] = set(adjacency.keys())

    ordered: List[str] = []
    temp_mark: Set[str] = set()
    perm_mark: Set[str] = set()

    def visit(node: str) -> None:
        if node in perm_mark:
            return
        if node in temp_mark:
            # Cycle detected; ignore the back-edge and stop deeper traversal
            return
        temp_mark.add(node)
        for child in adjacency.get(node, []):
            visit(child)
        temp_mark.remove(node)
        perm_mark.add(node)
        ordered.append(node)

    result: List[str] = []

    # Handle top-first traversal if applicable
    if top_module and top_module in hierarchical_modules:
        before_top_len = len(ordered)
        visit(top_module)
        top_subgraph_order = ordered[before_top_len:]
        # top_subgraph_order is children-first ending with top
        for name in top_subgraph_order:
            if name != top_module:
                result.append(name)
        # Orphans (deterministic iteration by module insertion order)
        for name in asdl_file.modules.keys():
            if name in hierarchical_modules and name not in perm_mark:
                visit(name)
                # append newly added nodes in this orphan component
                # Find slice boundary
                # (ordered accumulates globally; add any new nodes that appeared)
                # Ensure we don't duplicate already appended names
                
        for name in ordered:
            if name not in result and name != top_module:
                result.append(name)
        # Finally append top
        result.append(top_module)
        return result

    # No applicable top; traverse all hierarchical nodes deterministically
    for name in asdl_file.modules.keys():
        if name in hierarchical_modules and name not in perm_mark:
            visit(name)
    # 'ordered' already has children-first order for all components
    return ordered


