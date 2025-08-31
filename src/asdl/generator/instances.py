from __future__ import annotations

from typing import List

from ..data_structures import ASDLFile, Instance
from .templates import generate_primitive_instance
from .calls import generate_subckt_call


def generate_instance(instance_id: str, instance: Instance, asdl_file: ASDLFile, diagnostics: List) -> str:
    if instance.model not in asdl_file.modules:
        raise ValueError(f"Unknown model reference: {instance.model}")

    module = asdl_file.modules[instance.model]
    if module.spice_template is not None:
        return generate_primitive_instance(instance_id, instance, module, diagnostics)
    if module.instances is not None:
        return generate_subckt_call(instance_id, instance, asdl_file)
    raise ValueError(f"Module {instance.model} has neither spice_template nor instances")


