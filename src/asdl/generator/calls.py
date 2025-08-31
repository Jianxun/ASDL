from __future__ import annotations

from ..data_structures import ASDLFile, Instance
from .formatting import get_port_list, format_named_parameters


def generate_subckt_call(instance_id: str, instance: Instance, asdl_file: ASDLFile) -> str:
    module = asdl_file.modules[instance.model]

    node_list = []
    port_list = get_port_list(module)
    for port_name in port_list:
        if port_name in instance.mappings:
            node_list.append(instance.mappings[port_name])
        else:
            node_list.append("UNCONNECTED")

    instance_params = instance.parameters if instance.parameters else {}
    parts = [f"X_{instance_id}", " ".join(node_list), instance.model]
    if instance_params:
        parts.append(format_named_parameters(instance_params))
    return " ".join(parts)


