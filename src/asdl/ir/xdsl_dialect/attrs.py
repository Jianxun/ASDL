from __future__ import annotations

# Minimal attribute stubs to enable early registration and tests.
# These will be expanded with parsing/printing and verifiers in later phases.

try:  # Optional dependency: only import if xdsl is installed
    from xdsl.ir import Attribute
    from xdsl.irdl import IRDLOperation
    from xdsl.irdl import attr_def
except Exception:  # pragma: no cover - exercised only if optional dep missing
    Attribute = object  # type: ignore
    def attr_def(cls):  # type: ignore
        return cls


@attr_def
class PortAttr(Attribute):  # type: ignore[misc]
    # name: str, direction: str, kind: str
    pass


@attr_def
class RangeAttr(Attribute):  # type: ignore[misc]
    # msb: int, lsb: int
    pass


@attr_def
class ExprAttr(Attribute):  # type: ignore[misc]
    # textual expression placeholder; will be resolved in later passes
    pass


__all__ = [
    "PortAttr",
    "RangeAttr",
    "ExprAttr",
]


