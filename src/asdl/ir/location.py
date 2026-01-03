from __future__ import annotations

from typing import Optional

from xdsl.dialects.builtin import FileLineColLoc, LocationAttr

from asdl.diagnostics import SourcePos, SourceSpan


def location_attr_to_span(loc: LocationAttr | None) -> Optional[SourceSpan]:
    if loc is None:
        return None
    if isinstance(loc, FileLineColLoc):
        return SourceSpan(
            file=loc.filename.data,
            start=SourcePos(loc.line.data, loc.column.data),
            end=SourcePos(loc.line.data, loc.column.data),
        )
    return None


__all__ = ["location_attr_to_span"]
