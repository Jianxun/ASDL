from __future__ import annotations

from typing import Dict, List, Tuple

from ..data_structures import ASDLFile, Instance, Module
from .diagnostics import create_generator_diagnostic


def validate_model_exists(instance: Instance, asdl_file: ASDLFile, diagnostics: List) -> Tuple[bool, str]:
    if instance.model not in asdl_file.modules:
        diagnostics.append(create_generator_diagnostic("G0401", model=instance.model))
        return False, f"* ERROR G0401: unknown model '{instance.model}'"
    return True, ""


def validate_required_mappings(
    instance_id: str,
    instance: Instance,
    child_module: Module,
    diagnostics: List,
    required_ports: List[str],
) -> Tuple[bool, str]:
    provided = instance.mappings or {}
    missing = [p for p in required_ports if p not in provided]
    if missing:
        diagnostics.append(
            create_generator_diagnostic(
                "G0201", instance_id=instance_id, model=instance.model, missing=str(missing)
            )
        )
        return (
            False,
            f"* ERROR G0201: instance '{instance_id}' of '{instance.model}' missing mappings for: {missing}",
        )
    return True, ""


