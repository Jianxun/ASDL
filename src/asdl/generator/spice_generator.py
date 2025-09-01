"""
SPICE netlist generation implementation for ASDL.

Generates SPICE netlists from elaborated ASDL designs where patterns
have been expanded and parameters have been resolved.
"""

from typing import List, Optional, Tuple
from ..data_structures import ASDLFile, Module, Instance
from ..diagnostics import Diagnostic
from .diagnostics import create_generator_diagnostic
from .options import GeneratorOptions
from .subckt import build_subckt
from .ordering import compute_hierarchical_dependency_order
from .options import TopStyle
from .instances import generate_instance as _generate_instance_line
from .postprocess import check_unresolved_placeholders


class SPICEGenerator:
    """
    Unified SPICE netlist generator for ASDL designs.
    
    Generates SPICE netlists with unified module architecture:
    - Primitive modules (with spice_template) → inline SPICE generation
    - Hierarchical modules (with instances) → .subckt definitions
    - ngspice compatible output format
    
    Pipeline order:
    1. Hierarchical module subcircuit definitions (.subckt for each circuit module)
    2. End statement (.end)
    """
    

    
    def __init__(self, options: Optional[GeneratorOptions] = None):
        """Initialize SPICE generator with default settings."""
        self.comment_style = "*"  # SPICE comment character
        self.indent = ""        # Indentation for readability
        self._pending_diagnostics: List[Diagnostic] = []
        self.options = options or GeneratorOptions()
    
    def generate(self, asdl_file: ASDLFile) -> Tuple[str, List[Diagnostic]]:
        """Generate complete SPICE netlist from ASDL design."""
        lines: List[str] = []
        self._reset_run_state()
        self._append_header(lines, asdl_file)
        self._append_invalid_module_comments(lines, asdl_file)
        self._append_hierarchical_subckts(lines, asdl_file)
        self._append_top_diagnostics(lines, asdl_file)
        self._append_end(lines)
        final_spice = "\n".join(lines)
        diagnostics: List[Diagnostic] = []
        diagnostics.extend(check_unresolved_placeholders(final_spice))
        diagnostics.extend(self._pending_diagnostics)
        return final_spice, diagnostics

    # Orchestration helpers
    def _reset_run_state(self) -> None:
        self._pending_diagnostics = []

    def _append_header(self, lines: List[str], asdl_file: ASDLFile) -> None:
        lines.append(f"* SPICE netlist generated from ASDL")
        lines.append(f"* Design: {asdl_file.file_info.doc}")
        lines.append(f"* Top module: {asdl_file.file_info.top_module}")
        lines.append(f"* Author: {asdl_file.file_info.author}")
        lines.append(f"* Date: {asdl_file.file_info.date}")
        lines.append(f"* Revision: {asdl_file.file_info.revision}")
        lines.append("")

    def _append_invalid_module_comments(self, lines: List[str], asdl_file: ASDLFile) -> None:
        invalid_modules = [
            (name, module)
            for name, module in asdl_file.modules.items()
            if module.spice_template is None and module.instances is None
        ]
        for module_name, _module in invalid_modules:
            self._pending_diagnostics.append(create_generator_diagnostic("G0301", module=module_name))
            lines.append(
                f"* ERROR G0301: module '{module_name}' has neither spice_template nor instances"
            )
        if invalid_modules:
            lines.append("")

    def _append_hierarchical_subckts(self, lines: List[str], asdl_file: ASDLFile) -> None:
        # Determine hierarchical dependency order (children before parents, top last)
        top_name = asdl_file.file_info.top_module if asdl_file.file_info.top_module else None
        order = compute_hierarchical_dependency_order(asdl_file, top_name)
        if not order:
            return
        lines.append("* Hierarchical module subcircuit definitions")
        for module_name in order:
            module = asdl_file.modules[module_name]
            is_top = (top_name == module_name)
            comment_wrappers = is_top and self.options.top_style == TopStyle.FLAT
            subckt_def = build_subckt(
                module,
                module_name,
                asdl_file,
                self._pending_diagnostics,
                indent=self.indent,
                comment_top_wrappers=comment_wrappers,
            )
            lines.append(subckt_def)
            lines.append("")

    def _append_top_diagnostics(self, lines: List[str], asdl_file: ASDLFile) -> None:
        if asdl_file.file_info.top_module:
            top_module_name = asdl_file.file_info.top_module
            if top_module_name not in asdl_file.modules:
                available = sorted(asdl_file.modules.keys())
                self._pending_diagnostics.append(
                    create_generator_diagnostic(
                        "G0102", top_module=top_module_name, available=str(available)
                    )
                )
                lines.append(
                    f"* ERROR G0102: top module '{top_module_name}' not found; available: {available}"
                )
        else:
            self._pending_diagnostics.append(create_generator_diagnostic("G0701"))
            lines.append("* INFO G0701: no top module specified; skipping main instantiation")

    def _append_end(self, lines: List[str]) -> None:
        lines.append("")
        lines.append(".end")
    
    # Backwards-compatibility wrappers for unit tests
    def generate_subckt(self, module: Module, module_name: str, asdl_file: ASDLFile) -> str:
        return build_subckt(
            module,
            module_name,
            asdl_file,
            self._pending_diagnostics,
            indent=self.indent,
        )

    def generate_instance(self, instance_id: str, instance: Instance, asdl_file: ASDLFile) -> str:
        return _generate_instance_line(instance_id, instance, asdl_file, self._pending_diagnostics)
    
    
    
    
    
    # Removed legacy helpers (_get_top_level_nets, _format_parameter_value, _check_unresolved_placeholders)


