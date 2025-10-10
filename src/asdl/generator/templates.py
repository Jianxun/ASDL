from __future__ import annotations

from typing import Dict, List

from ..data_structures import Instance, Module
from .diagnostics import create_generator_diagnostic


def generate_primitive_instance(
    instance_id: str, instance: Instance, module: Module, diagnostics: List
) -> str:
    if not module.spice_template:
        raise ValueError(f"Module {instance_id} has no spice_template for primitive generation")

    template_data: Dict[str, object] = {}
    template_data["name"] = instance_id

    if instance.mappings:
        for port_name, net_name in instance.mappings.items():
            template_data[port_name] = net_name

    merged_params: Dict[str, object] = {}
    if module.parameters:
        merged_params.update(module.parameters)
    if instance.parameters:
        merged_params.update(instance.parameters)
    for param_name, param_value in merged_params.items():
        template_data[param_name] = param_value

    if module.variables:
        for var_name, var_value in module.variables.items():
            if var_name in template_data:
                diagnostics.append(
                    create_generator_diagnostic(
                        "G0601", param=var_name, instance_id=instance_id, model=instance.model
                    )
                )
            template_data[var_name] = var_value

    class _DefaultingDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"

    # Protect Jinja-style double braces so Python .format_map doesn't collapse them
    template_str = module.spice_template.replace("{{", "__J2_L__").replace("}}", "__J2_R__")
    formatted = template_str.format_map(_DefaultingDict(template_data))
    # Restore Jinja double braces for downstream template flows and diagnostics
    return formatted.replace("__J2_L__", "{{").replace("__J2_R__", "}}")


