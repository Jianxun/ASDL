from typing import List, Tuple, Dict, Any, Optional
from dataclasses import replace
import re

from asdl.data_structures import ASDLFile, Module, Port, Locatable, Instance
from asdl.diagnostics import Diagnostic, DiagnosticSeverity


class Elaborator:
    """
    The Elaborator is responsible for transforming the raw, parsed ASDL data
    structures into a fully specified, elaborated design. It handles:
    - Pattern Expansion (both literal <> and bus [])
    - Parameter Resolution (future implementation)
    """

    def elaborate(
        self, asdl_file: ASDLFile
    ) -> Tuple[Optional[ASDLFile], List[Diagnostic]]:
        """
        Elaborates an ASDL file by performing pattern expansion.
        """
        diagnostics: List[Diagnostic] = []

        try:
            elaborated_file = replace(asdl_file, modules={})
            for name, module in asdl_file.modules.items():
                elaborated_module, module_diagnostics = self._elaborate_module(module)
                diagnostics.extend(module_diagnostics)
                elaborated_file.modules[name] = elaborated_module

            return elaborated_file, diagnostics

        except Exception as e:
            diagnostics.append(
                self._create_diagnostic(
                    "E999", "Internal Elaboration Error", f"An unexpected error occurred: {e}"
                )
            )
            return None, diagnostics

    def _elaborate_module(self, module: Module) -> Tuple[Module, List[Diagnostic]]:
        """
        Expand patterns within a single module.
        """
        diagnostics: List[Diagnostic] = []
        # Create a deep copy to avoid modifying the original during iteration
        module_copy = replace(
            module,
            ports={name: replace(port) for name, port in (module.ports or {}).items()},
            instances={
                name: replace(inst) for name, inst in (module.instances or {}).items()
            },
        )

        expanded_ports, port_diagnostics = self._expand_ports(module_copy.ports)
        diagnostics.extend(port_diagnostics)
        module_copy.ports = expanded_ports

        # TODO: A similar expansion is needed for instances
        # expanded_instances, instance_diagnostics = self._expand_instances(module_copy.instances)
        # diagnostics.extend(instance_diagnostics)
        # module_copy.instances = expanded_instances

        return module_copy, diagnostics

    def _expand_ports(
        self, ports: Optional[Dict[str, Port]]
    ) -> Tuple[Dict[str, Port], List[Diagnostic]]:
        if not ports:
            return {}, []

        new_ports = {}
        diagnostics: List[Diagnostic] = []

        for port_name, port_obj in ports.items():
            has_literal = self._has_literal_pattern(port_name)
            has_bus = self._has_bus_pattern(port_name)

            if has_literal and has_bus:
                diagnostics.append(
                    self._create_diagnostic(
                        "E103",
                        "Mixed Pattern Types",
                        f"Port '{port_name}' contains both a literal ('<>') and bus ('[]') pattern.",
                        port_obj,
                    )
                )
                new_ports[port_name] = port_obj  # Keep original on error
                continue

            if has_literal:
                expanded_names, literal_diagnostics = self._expand_literal_pattern(
                    port_name, port_obj
                )
                diagnostics.extend(literal_diagnostics)
                if not literal_diagnostics:
                    for new_name in expanded_names:
                        new_ports[new_name] = replace(port_obj)
                else:
                    new_ports[port_name] = port_obj
            elif has_bus:
                expanded_names, bus_diagnostics = self._expand_bus_pattern(
                    port_name, port_obj
                )
                diagnostics.extend(bus_diagnostics)
                if not bus_diagnostics:
                    for new_name in expanded_names:
                        new_ports[new_name] = replace(port_obj)
                else:
                    new_ports[port_name] = port_obj
            else:
                new_ports[port_name] = port_obj

        return new_ports, diagnostics

    def _has_literal_pattern(self, name: str) -> bool:
        return bool(re.search(r"<.+>", name))

    def _has_bus_pattern(self, name: str) -> bool:
        return bool(re.search(r"\[\d+:\d+\]$", name))

    def _expand_literal_pattern(
        self, name: str, locatable: Locatable
    ) -> Tuple[List[str], List[Diagnostic]]:
        # This is a placeholder for the real implementation
        match = re.search(r"^(.*?)<(.+?)>(.*?)$", name)
        if not match:
            return [name], []
        prefix, content, suffix = match.groups()
        items = [item.strip() for item in content.split(",")]
        # NOTE: Assumes existing validation logic for E100, E101, E107 is here
        return [f"{prefix}{item}{suffix}" for item in items], []

    def _expand_bus_pattern(
        self, name: str, locatable: Locatable
    ) -> Tuple[List[str], List[Diagnostic]]:
        diagnostics = []
        match = re.search(r"^(.*)\[(\d+):(\d+)\]$", name)
        if not match:
            return [name], diagnostics

        base_name, msb_str, lsb_str = match.groups()
        msb, lsb = int(msb_str), int(lsb_str)

        if msb == lsb:
            diagnostics.append(
                self._create_diagnostic(
                    "E104",
                    "Invalid Bus Range",
                    f"Bus range '{name}' has identical MSB and LSB.",
                    locatable,
                )
            )
            return [], diagnostics

        if msb < lsb:
            return [f"{base_name}{i}" for i in range(msb, lsb + 1)], diagnostics
        else:
            return [f"{base_name}{i}" for i in range(msb, lsb - 1, -1)], diagnostics

    def _create_diagnostic(
        self,
        code: str,
        title: str,
        details: str,
        locatable: Optional[Locatable] = None,
    ) -> Diagnostic:
        """Helper to create a diagnostic object with location info."""
        return Diagnostic(
            code=code,
            title=title,
            details=details,
            severity=DiagnosticSeverity.ERROR, # Defaulting to ERROR for now
            location=locatable,
        ) 