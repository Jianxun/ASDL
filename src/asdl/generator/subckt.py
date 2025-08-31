from __future__ import annotations

from typing import List

from ..data_structures import ASDLFile, Module
from .formatting import get_port_list
from .guards import validate_model_exists, validate_required_mappings
from .instances import generate_instance


def build_subckt(
    module: Module,
    module_name: str,
    asdl_file: ASDLFile,
    diagnostics: List,
    indent: str = "  ",
    *,
    comment_top_wrappers: bool = False,
) -> str:
    lines: List[str] = []

    if module.doc:
        lines.append(f"* {module.doc}")

    port_list = get_port_list(module)
    subckt_line = f".subckt {module_name} {' '.join(port_list)}"
    lines.append(f"* {subckt_line}" if comment_top_wrappers else subckt_line)

    if module.instances:
        for instance_id, instance in module.instances.items():
            if instance.doc:
                lines.append(f"{indent}* {instance.doc}")

            ok, msg = validate_model_exists(instance, asdl_file, diagnostics)
            if not ok:
                lines.append(f"{indent}{msg}")
                continue

            child_module = asdl_file.modules[instance.model]
            required_ports = get_port_list(child_module)
            ok, msg = validate_required_mappings(instance_id, instance, child_module, diagnostics, required_ports)
            if not ok:
                lines.append(f"{indent}{msg}")
                continue

            instance_line = generate_instance(instance_id, instance, asdl_file, diagnostics)
            lines.append(f"{indent}{instance_line}")

    end_line = ".ends"
    lines.append(f"* {end_line}" if comment_top_wrappers else end_line)
    return "\n".join(lines)


