from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from asdl.ast import AsdlDocument, DeviceDecl, ModuleDecl
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, SourceSpan

from .diagnostics import duplicate_symbol


@dataclass
class ProgramDB:
    documents: Dict[str, AsdlDocument] = field(default_factory=dict)
    modules: Dict[tuple[str, str], ModuleDecl] = field(default_factory=dict)
    devices: Dict[tuple[str, str], DeviceDecl] = field(default_factory=dict)

    def add_document(self, file_id: str, document: AsdlDocument) -> List[Diagnostic]:
        if file_id in self.documents:
            return []

        diagnostics: List[Diagnostic] = []
        seen: Dict[str, str] = {}

        for name, decl in (document.modules or {}).items():
            if _is_duplicate(name, "module", seen):
                diagnostics.append(duplicate_symbol(name, span=_span_from_loc(decl)))
                continue
            self.modules[(file_id, name)] = decl

        for name, decl in (document.devices or {}).items():
            if _is_duplicate(name, "device", seen):
                diagnostics.append(duplicate_symbol(name, span=_span_from_loc(decl)))
                continue
            self.devices[(file_id, name)] = decl

        self.documents[file_id] = document
        return diagnostics


def _is_duplicate(name: str, kind: str, seen: Dict[str, str]) -> bool:
    if name in seen:
        return True
    seen[name] = kind
    return False


def _span_from_loc(value: object) -> SourceSpan | None:
    loc = getattr(value, "_loc", None)
    if isinstance(loc, Locatable):
        return loc.to_source_span()
    return None


__all__ = ["ProgramDB"]
