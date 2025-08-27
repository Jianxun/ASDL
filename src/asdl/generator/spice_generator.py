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
        self.indent = "  "        # Indentation for readability
        self._pending_diagnostics: List[Diagnostic] = []
        self.options = options or GeneratorOptions()
    
    def generate(self, asdl_file: ASDLFile) -> Tuple[str, List[Diagnostic]]:
        """
        Generate complete SPICE netlist from ASDL design with unified architecture.
        
        Args:
            asdl_file: Fully elaborated ASDL design
            
        Returns:
            Tuple of (complete SPICE netlist as string, list of diagnostics)
        """
        lines = []
        diagnostics: List[Diagnostic] = []
        
        # Reset pending diagnostics for this run
        self._pending_diagnostics = []

        # Add header comment
        lines.append(f"* SPICE netlist generated from ASDL")
        lines.append(f"* Design: {asdl_file.file_info.doc}")
        lines.append(f"* Top module: {asdl_file.file_info.top_module}")
        lines.append(f"* Author: {asdl_file.file_info.author}")
        lines.append(f"* Date: {asdl_file.file_info.date}")
        lines.append(f"* Revision: {asdl_file.file_info.revision}")
        lines.append("")
        
        # Detect invalid modules (neither primitive nor hierarchical)
        invalid_modules = [
            (name, module)
            for name, module in asdl_file.modules.items()
            if module.spice_template is None and module.instances is None
        ]
        for module_name, _module in invalid_modules:
            # Emit diagnostic and add helpful comment; skip generation for that module
            self._pending_diagnostics.append(
                create_generator_diagnostic("G0301", module=module_name)
            )
            lines.append(
                f"* ERROR G0301: module '{module_name}' has neither spice_template nor instances"
            )
        if invalid_modules:
            lines.append("")

        # Generate subcircuit definitions for hierarchical modules only
        # (primitive modules are handled inline)
        hierarchical_modules = {name: module for name, module in asdl_file.modules.items() 
                               if module.instances is not None}
        
        
        if hierarchical_modules:
            lines.append("* Hierarchical module subcircuit definitions")
            for module_name, module in hierarchical_modules.items():
                subckt_def = build_subckt(
                    module,
                    module_name,
                    asdl_file,
                    self._pending_diagnostics,
                    indent=self.indent,
                )
                lines.append(subckt_def)
                lines.append("")
        
        # Top-level instantiation removed in refactor. Preserve diagnostics behavior.
        if asdl_file.file_info.top_module:
            top_module_name = asdl_file.file_info.top_module
            if top_module_name not in asdl_file.modules:
                available = sorted(asdl_file.modules.keys())
                self._pending_diagnostics.append(
                    create_generator_diagnostic(
                        "G0102",
                        top_module=top_module_name,
                        available=str(available),
                    )
                )
                lines.append(
                    f"* ERROR G0102: top module '{top_module_name}' not found; available: {available}"
                )
        else:
            self._pending_diagnostics.append(
                create_generator_diagnostic("G0701")
            )
            lines.append("* INFO G0701: no top module specified; skipping main instantiation")
        
        # End SPICE netlist (ngspice compatibility)
        lines.append("")
        lines.append(".end")
        
        # Check for unresolved placeholders in the final SPICE output
        final_spice = "\n".join(lines)
        placeholder_diagnostics = check_unresolved_placeholders(final_spice)
        diagnostics.extend(placeholder_diagnostics)
        # Include any diagnostics collected during generation
        diagnostics.extend(self._pending_diagnostics)
        
        return final_spice, diagnostics
    
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


