from __future__ import annotations

from typing import List, Dict

from ..data_structures import ASDLFile, Module, Port, Instance


def _fmt_kv_pairs(d: dict | None) -> str:
    if not d:
        return "{}"
    items = ", ".join(f"{k}={repr(v)}" for k, v in d.items())
    return "{" + items + "}"


def _format_port(name: str, port: Port) -> str:
    dir_str = getattr(port.dir, "value", str(port.dir))
    kind_str = getattr(port.type, "value", str(port.type))
    return f"%port {name} dir={dir_str} kind={kind_str}"


def _format_instance(inst_id: str, inst: Instance) -> str:
    # mappings: Dict[port_name, net_name]
    mappings_str = _fmt_kv_pairs(inst.mappings)
    params = _fmt_kv_pairs(inst.parameters)
    return f"%inst {inst_id}: model={inst.model} mappings={mappings_str} params={params}"


def _format_module(name: str, mod: Module) -> List[str]:
    lines: List[str] = []
    ports: Dict[str, Port] = mod.ports or {}
    instances: Dict[str, Instance] = mod.instances or {}
    params = _fmt_kv_pairs(mod.parameters)
    lines.append(f"module @{name} params={params}")
    for port_name, port in ports.items():
        lines.append("  " + _format_port(port_name, port))
    for inst_id, inst in instances.items():
        lines.append("  " + _format_instance(inst_id, inst))
    lines.append("endmodule")
    return lines


def build_textual_ir(asdl_file: ASDLFile) -> str:
    """
    Produce a minimal textual IR snapshot from the AST.

    This is a stop-gap for Phase 0 to validate the CLI and data plumbing.
    It is intentionally simple and will be replaced by xDSL printing.
    """
    lines: List[str] = []
    fi = asdl_file.file_info
    top = getattr(fi, "top_module", None)
    doc = getattr(fi, "doc", None)
    header_parts = [
        p for p in [f"top={top}" if top else None, f"doc={doc!r}" if doc else None]
        if p is not None
    ]
    header = " ".join(header_parts)
    lines.append(f"asdl.module_set {header}".strip())

    for name, mod in (asdl_file.modules or {}).items():
        lines.extend(_format_module(name, mod))

    return "\n".join(lines) + "\n"


