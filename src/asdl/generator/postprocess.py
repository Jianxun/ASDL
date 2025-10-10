from __future__ import annotations

import re
from typing import List

from ..diagnostics import Diagnostic
from .diagnostics import create_generator_diagnostic
from .options import GeneratorOptions


def check_unresolved_placeholders(spice_output: str, options: GeneratorOptions) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    # Skip all placeholder checks in template mode
    if options.template_mode:
        return diagnostics

    # Find single-brace placeholders like {name}
    single_brace_pattern = re.compile(r"(?<!\{)\{([^{][^{}]*)\}(?!\})")
    single_matches = single_brace_pattern.findall(spice_output)

    if single_matches:
        unique_single = sorted(set(m.strip() for m in single_matches))
        placeholder_list = ", ".join(f"'{{{name}}}'" for name in unique_single)
        diagnostics.append(
            create_generator_diagnostic("G0305", placeholders=placeholder_list, location=None)
        )

    # Find double-brace Jinja placeholders like {{ name }}
    double_brace_pattern = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")
    double_matches = double_brace_pattern.findall(spice_output)
    if double_matches:
        unique_double = sorted(set(m.strip() for m in double_matches))
        placeholder_list = ", ".join(f"'{{{{ {name} }}}}'" for name in unique_double)
        diagnostics.append(
            create_generator_diagnostic(
                "G0602",
                placeholders=placeholder_list,
                location=None,
                suggestion="Pass --template to output a .j2 file and suppress placeholder warnings.",
            )
        )

    return diagnostics


