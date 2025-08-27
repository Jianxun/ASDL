from __future__ import annotations

import re
from typing import List

from ..diagnostics import Diagnostic
from .diagnostics import create_generator_diagnostic


def check_unresolved_placeholders(spice_output: str) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    pattern = re.compile(r"\{([^}]+)\}")
    matches = pattern.findall(spice_output)
    if matches:
        unique = sorted(set(matches))
        placeholder_list = ", ".join(f"'{{{name}}}'" for name in unique)
        diagnostics.append(
            create_generator_diagnostic("G0305", placeholders=placeholder_list, location=None)
        )
    return diagnostics


