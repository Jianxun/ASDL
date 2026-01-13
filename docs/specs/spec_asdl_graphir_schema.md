# ASDL GraphIR Dialect Schema

Status: Draft

## 1. Purpose

This document defines the concrete GraphIR dialect schema (ops and attributes).
It complements the conceptual GraphIR specification.

## 2. GraphIR Ops

```
graphir.program {
  entry: GraphId?
  file_order: list[str]
} {
  graphir.module*
  graphir.device*
}

graphir.module {
  module_id: GraphId
  name: str
  file_id: str
  attrs: dict?
  annotations: dict?
  emit_name: str?
  emit_name_locked: bool?
} {
  graphir.net*
  graphir.instance*
  graphir.bundle*
  graphir.pattern_expr*
  graphir.detached
}

graphir.device {
  device_id: GraphId
  name: str
  file_id: str
  ports: list[str]
  params: dict?
  annotations: dict?
} {
  graphir.backend*
}

graphir.net {
  net_id: GraphId
  name: str
  attrs: dict?
  annotations: dict?
} {
  graphir.endpoint*
}

graphir.instance {
  inst_id: GraphId
  name: str
  module_ref: SymbolRef
  module_ref_raw: str
  props: dict?
  annotations: dict?
}

graphir.endpoint {
  endpoint_id: GraphId
  inst_id: GraphId
  port_path: str
}

graphir.bundle {
  bundle_id: GraphId
  kind: "net" | "endpoint" | "param" | "inst"
  base_name: str
  pattern_type: "literal" | "numeric"
  members: list[BundleMember]
  annotations: dict?
}

graphir.pattern_expr {
  pattern_id: GraphId
  kind: "net" | "endpoint" | "param" | "inst"
  owner: PatternOwner
  bundles: list[BundleId]
  annotations: dict?
}

graphir.detached {
  graphir.endpoint*
}

graphir.backend {
  name: str
  template: str
  params: dict?
  props: dict?
}

BundleMember = net_id | inst_id | endpoint_id | param_ref
param_ref = { inst_id, name, index? }
SymbolRef = { kind: "module" | "device", id: GraphId }
PatternOwner = net_id | endpoint_id | inst_id | param_ref
```

### Module attrs (reserved keys)
- `port_order`: list[str]
  - Ordered list of port net names derived from `$` nets.
  - Names are stored without the `$` prefix and are literal (post-expansion).
