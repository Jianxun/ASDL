from __future__ import annotations

"""
Pass hooks for the ASDL xDSL engine (Phase 0): no-op placeholders.

These functions provide a stable surface to plug pass names without
implementing any transformation yet.
"""

from typing import Iterable


def run_passes(_mlctx, _module_op, pass_names: Iterable[str]) -> None:
    """
    Run a sequence of passes by name. Phase 0: no-ops.
    """
    # Intentionally do nothing for now. This is the extension point.
    for _name in pass_names:
        # Placeholder: later we will dispatch to real passes
        continue


