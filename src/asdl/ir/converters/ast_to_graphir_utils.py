"""Utility helpers for AST to GraphIR conversion."""

from __future__ import annotations

from typing import Dict, Optional

from xdsl.dialects.builtin import (
    DictionaryAttr,
    FileLineColLoc,
    IntAttr,
    LocationAttr,
    StringAttr,
)

from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity

NO_SPAN_NOTE = "No source span available."


def to_string_dict_attr(
    values: Optional[Dict[str, object]],
) -> Optional[DictionaryAttr]:
    """Convert a dictionary to a DictionaryAttr of string values.

    Args:
        values: Optional parameter mapping.

    Returns:
        DictionaryAttr of StringAttr values or None.
    """
    if not values:
        return None
    items = {key: StringAttr(_format_param_value(value)) for key, value in values.items()}
    return DictionaryAttr(items)


def loc_attr(loc: Optional[Locatable]) -> Optional[LocationAttr]:
    """Convert a locatable payload into an xDSL location attribute.

    Args:
        loc: Optional location metadata from the AST.

    Returns:
        FileLineColLoc when location data is available; otherwise None.
    """
    if (
        loc is None
        or loc.start_line is None
        or loc.start_col is None
        or not loc.file
    ):
        return None
    return FileLineColLoc(
        StringAttr(loc.file), IntAttr(loc.start_line), IntAttr(loc.start_col)
    )


def maybe_src_annotations(loc: Optional[Locatable]) -> Optional[DictionaryAttr]:
    """Build an annotations dictionary containing source metadata.

    Args:
        loc: Optional location metadata from the AST.

    Returns:
        DictionaryAttr containing a "src" entry or None when unavailable.
    """
    src = loc_attr(loc)
    if src is None:
        return None
    return DictionaryAttr({"src": src})


def diagnostic(
    code: str,
    message: str,
    loc: Optional[Locatable],
    severity: Severity = Severity.ERROR,
) -> Diagnostic:
    """Create a diagnostic from a source location.

    Args:
        code: Diagnostic code.
        message: Diagnostic message.
        loc: Optional source location.
        severity: Diagnostic severity.

    Returns:
        Diagnostic instance.
    """
    span = loc.to_source_span() if loc is not None else None
    notes = None if span is not None else [NO_SPAN_NOTE]
    return Diagnostic(
        code=code,
        severity=severity,
        message=message,
        primary_span=span,
        notes=notes,
        source="ir",
    )


def _format_param_value(value: object) -> str:
    """Format parameter values as strings.

    Args:
        value: Parameter value.

    Returns:
        Serialized string representation.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


__all__ = ["diagnostic", "loc_attr", "maybe_src_annotations", "to_string_dict_attr"]
