import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click

from ..parser.asdl_parser import ASDLParser
from ..data_structures.structures import ASDLFile, Module, PortDirection


def _detect_flavor(model: str) -> Optional[str]:
    last = model.split('.')[-1].lower()
    if last.startswith('nmos'):
        return 'nmos'
    if last.startswith('pmos'):
        return 'pmos'
    return None


def _port_side_from_dir(direction: PortDirection) -> str:
    if direction == PortDirection.OUT:
        return 'right'
    # IN and IN_OUT default to left for MVP
    return 'left'


def _reuse_positions(nodes: List[Dict], prior: Dict[str, Dict[str, int]]) -> None:
    for n in nodes:
        nid = n['id']
        if nid in prior:
            n['position'] = dict(prior[nid])


def _autoplace(nodes: List[Dict], grid: int) -> None:
    # Simple columns: ports left/right, transistors center
    left_x = 4
    right_x = 36
    mid_x = 20
    left_y = 6
    right_y = 6
    mid_y = 6
    spacing = 3

    for n in nodes:
        if 'position' in n and n['position']:
            continue
        if n['type'] == 'port':
            side = n['data'].get('side', 'left')
            if side == 'right':
                n['position'] = {'gx': right_x, 'gy': right_y}
                right_y += spacing
            else:
                n['position'] = {'gx': left_x, 'gy': left_y}
                left_y += spacing
        else:
            n['position'] = {'gx': mid_x, 'gy': mid_y}
            mid_y += spacing


def _build_graph_for_module(asdl: ASDLFile, module_name: str, grid_size: int,
                            prior_layout: Optional[Dict[str, Dict[str, int]]] = None) -> Dict:
    if module_name not in asdl.modules:
        raise click.ClickException(f"Module not found: {module_name}")
    mod: Module = asdl.modules[module_name]
    if mod.ports is None:
        ports: Dict[str, object] = {}
    else:
        ports = mod.ports

    nodes: List[Dict] = []
    edges: List[Dict] = []

    # Port nodes
    for pname, p in ports.items():
        side = _port_side_from_dir(p.dir)
        nodes.append({
            'id': pname,
            'type': 'port',
            'data': {'name': pname, 'side': side}
        })

    # Instance nodes (MOSFETs only for MVP)
    if mod.instances:
        for inst_name, inst in mod.instances.items():
            flavor = _detect_flavor(inst.model)
            if not flavor:
                continue
            nodes.append({
                'id': inst_name,
                'type': 'transistor',
                'data': {'name': inst_name, 'flavor': flavor}
            })

    # Edges: build net -> endpoints
    net_to_eps: Dict[str, List[Tuple[str, str]]] = {}
    # Port endpoints
    for pname in ports.keys():
        net_to_eps.setdefault(pname, []).append((pname, 'P'))
    # Instance endpoints from mappings
    if mod.instances:
        for inst_name, inst in mod.instances.items():
            flavor = _detect_flavor(inst.model)
            if not flavor:
                continue
            for pin, net in inst.mappings.items():
                up = pin.upper()
                if up in ('D','G','S'):
                    net_to_eps.setdefault(net, []).append((inst_name, up))

    # Emit edges: hub=port if present else first
    for net, eps in net_to_eps.items():
        if len(eps) < 2:
            continue
        hub_idx = 0
        for i, (nid, hid) in enumerate(eps):
            if hid == 'P':
                hub_idx = i
                break
        hub_n, hub_h = eps[hub_idx]
        for i, (nid, hid) in enumerate(eps):
            if i == hub_idx:
                continue
            edges.append({
                'source': hub_n,
                'sourceHandle': hub_h,
                'target': nid,
                'targetHandle': hid,
            })

    # Positions
    if prior_layout:
        _reuse_positions(nodes, prior_layout)
    _autoplace(nodes, grid_size)

    return {
        'gridSize': grid_size,
        'nodes': nodes,
        'edges': edges,
    }


@click.command(name='visualize', help='Export a module-scoped visualization graph JSON (no elaboration).')
@click.option('--module', 'module_name', required=True, help='Module name to export (exact, in the given ASDL file).')
@click.option('--in', 'in_file', required=True, type=click.Path(exists=True, dir_okay=False), help='Input ASDL file path.')
@click.option('--out', 'out_file', default='prototype/visualizer_react_flow/public/graph.json', show_default=True,
              type=click.Path(dir_okay=False), help='Output graph JSON path.')
@click.option('--grid', 'grid_size', default=16, show_default=True, type=int, help='Grid size (pixels).')
@click.option('--reuse', 'reuse_layout', type=click.Path(exists=True, dir_okay=False), help='Prior graph.json to reuse positions from (by node id).')
def visualize_cmd(module_name: str, in_file: str, out_file: str, grid_size: int, reuse_layout: Optional[str]) -> None:
    parser = ASDLParser()
    asdl, diags = parser.parse_file(in_file)
    if asdl is None:
        raise click.ClickException('Failed to parse ASDL file.')

    prior_map: Optional[Dict[str, Dict[str, int]]] = None
    if reuse_layout:
        try:
            with open(reuse_layout, 'r', encoding='utf-8') as f:
                prior = json.load(f)
            prior_nodes = prior.get('nodes', [])
            prior_map = {n['id']: n.get('position', {}) for n in prior_nodes if isinstance(n, dict) and 'id' in n}
        except Exception:
            prior_map = None

    graph = _build_graph_for_module(asdl, module_name, grid_size, prior_map)

    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, indent=2)
    click.echo(f"Wrote graph JSON: {out_path}")


