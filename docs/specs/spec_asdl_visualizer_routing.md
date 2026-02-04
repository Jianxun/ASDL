# ASDL Visualizer Routing (Prototype)

## Inputs
### PatternedGraph JSON
Produced by `asdl patterned-graph-dump`. This is the single source of truth
for connectivity and pattern metadata. The visualizer reads:
- `modules`, `nets`, `instances`, `endpoints`
- `registries.pattern_expressions`, `pattern_origins`, `schematic_hints`

## Derived visualizer graph
The renderer builds an explicit node+edge graph:
- Nodes: instances, net hubs, optional port/junction helpers.
- Edges: topology-specific routed edges (see "Routing topologies").
- Handle IDs: pin names for instance/port pins; `hub` for net hubs.
Routing is always derived from the current layout (instance/hub positions and
orientation). Any placement/orientation change must recompute the routed edges
for the affected nets.

## Routing topologies (per net group)
Topology selection is per net and applies independently to each hub group. If
`schematic_hints.net_groups` is present for a net, endpoints are partitioned
into groups; group index maps to hub group index based on hub order. Each group
uses the same `topology` value and the corresponding hub placement.

Topologies:
- `star` (default): connect each endpoint directly to the hub with a single
  rectilinear segment (pin-to-hub).
- `mst`: build a Manhattan minimum spanning tree over the endpoint nodes plus
  the hub (the hub is an MST node). Edge weights are Manhattan distances
  between node positions. Use a deterministic tie-breaker so routing is stable:
  sort candidate edges by `(distance, node_key_a, node_key_b)` where node keys
  follow the stable endpoint order (net group order, then endpoint order within
  the group) and the hub sorts first. Any valid deterministic MST algorithm is
  acceptable (e.g., Kruskal with the ordered edges). MST routing must be
  recomputed whenever layout changes.
- `trunk`: create a single rectilinear trunk line through the hub center and
  branch to endpoints with orthogonal drops. Trunk orientation follows the hub
  orientation: horizontal for `R0`, `R180`, `MX`, `MY`; vertical for `R90`,
  `R270`, `MXR90`, `MYR90`. If hub placement is missing, default to horizontal.
  The trunk extends in both directions along its axis from the minimum to
  maximum endpoint projection (so endpoints "behind" the hub are still
  reachable). Each endpoint connects to the trunk at its orthogonal
  projection, creating a junction node where the branch meets the trunk. No
  intermediate anchors are introduced beyond these trunk junctions.

## Connection labeling (numeric patterns)
For numeric patterns, the visualizer stays compact (no instance explosion) and
renders edge labels at the **pin**. Label formatting mirrors authored pattern
syntax:
- Single numeric index: `<3>`
- Multi-axis: tuple style, e.g. `<3,1>`
- When multiple slices are forced at a pin (see below), join with `;`
  following the slice syntax in `docs/specs/spec_asdl_pattern_expansion.md`.

Pin-level net label policy can override the default behavior:
- Pin `connect_by_label: true`: always render a label at the pin even when the
  edge provides no numeric pattern label. The label uses the net/slice naming
  (join multiple slices with `;`). The net/slice label is positioned just
  outside the symbol body, adjacent to the pin handle. When `connect_by_label`
  is true, the wire between the pin and net hub is suppressed. Pin name labels
  are independent and render inside the symbol body when `visible` is true.

## Rendering rules
1) **Identity**: use explicit edges only; never connect by name or pattern.
2) **Crossings**: edge overlap is never connectivity. Only junction nodes connect.
3) **Junctions**: render as a small filled dot at the junction node.
4) **Grid**: positions are snapped to the module `grid_size`.
5) **Patterns**: render bundles as labels; do not expand patterns in the UI.
6) **Labels**: pin name labels and hub labels rotate with orientation but are
   never upside down; vertical text reads bottom-to-top. Pin name labels render
   inside the body edge with a fixed inset. Net/slice labels render just outside
   the body edge adjacent to the pin handle.

## Differential nets
- A net with `atoms: ["P","N"]` is a diff net. Default render: a single bundled
  thick line between endpoints.
- At each endpoint, if the pin atom order differs from the net order, show a
  small swap glyph next to the net/slice label (e.g., `swap` icon).
- Optional debug view: render two thin lines (P and N) near the endpoint only.

Example binding (swapped polarity):
- Net: `stg1_out` atoms `["P","N"]`
- `MN_STG1.D` binds `["P","N"]` (no swap)
- `MN_STG2.G` binds `["N","P"]` (swap glyph)
