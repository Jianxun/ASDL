from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from asdl.ast import AsdlDocument, DeviceDecl, ModuleDecl
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic, Severity

from .diagnostics import DUPLICATE_SYMBOL, _diagnostic


@dataclass(frozen=True)
class SymbolRecord:
    name: str
    kind: str
    node: ModuleDecl | DeviceDecl
    loc: Optional[Locatable]


@dataclass
class ProgramDB:
    documents: Dict[str, AsdlDocument] = field(default_factory=dict)
    modules: Dict[tuple[str, str], ModuleDecl] = field(default_factory=dict)
    devices: Dict[tuple[str, str], DeviceDecl] = field(default_factory=dict)
    symbols_by_file: Dict[str, Dict[str, SymbolRecord]] = field(default_factory=dict)

    def register_document(self, file_id: str, document: AsdlDocument) -> List[Diagnostic]:
        if file_id in self.documents:
            return []

        diagnostics: List[Diagnostic] = []
        symbols: Dict[str, SymbolRecord] = {}

        self.documents[file_id] = document

        if document.modules:
            for name, module in document.modules.items():
                diagnostics.extend(
                    self._register_symbol(
                        symbols,
                        file_id,
                        name,
                        "module",
                        module,
                    )
                )

        if document.devices:
            for name, device in document.devices.items():
                diagnostics.extend(
                    self._register_symbol(
                        symbols,
                        file_id,
                        name,
                        "device",
                        device,
                    )
                )

        self.symbols_by_file[file_id] = symbols
        return diagnostics

    def _register_symbol(
        self,
        symbols: Dict[str, SymbolRecord],
        file_id: str,
        name: str,
        kind: str,
        node: ModuleDecl | DeviceDecl,
    ) -> List[Diagnostic]:
        if name in symbols:
            loc = getattr(node, "_loc", None)
            return [
                _diagnostic(
                    DUPLICATE_SYMBOL,
                    f"Duplicate symbol name '{name}' in '{file_id}'",
                    Severity.ERROR,
                    loc=loc,
                )
            ]

        record = SymbolRecord(
            name=name,
            kind=kind,
            node=node,
            loc=getattr(node, "_loc", None),
        )
        symbols[name] = record
        if kind == "module":
            self.modules[(file_id, name)] = node
        else:
            self.devices[(file_id, name)] = node
        return []


__all__ = ["ProgramDB", "SymbolRecord"]
