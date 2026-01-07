from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from asdl.ast import AsdlDocument, DeviceDecl, ModuleDecl
from asdl.ast.location import Locatable
from asdl.diagnostics import Diagnostic

from .diagnostics import import_duplicate_symbol

SymbolKind = str


@dataclass(frozen=True)
class SymbolDef:
    file_id: Path
    name: str
    kind: SymbolKind
    decl: ModuleDecl | DeviceDecl
    loc: Optional[Locatable] = None


@dataclass(frozen=True)
class ProgramDB:
    documents: Dict[Path, AsdlDocument]
    symbols: Dict[Path, Dict[str, SymbolDef]]

    @classmethod
    def build(
        cls, documents: Dict[Path, AsdlDocument]
    ) -> Tuple["ProgramDB", List[Diagnostic]]:
        diagnostics: List[Diagnostic] = []
        symbols: Dict[Path, Dict[str, SymbolDef]] = {}

        for file_id, document in documents.items():
            file_symbols: Dict[str, SymbolDef] = {}
            for name, module in _iter_modules(document):
                _register_symbol(
                    file_symbols,
                    diagnostics,
                    file_id,
                    name,
                    "module",
                    module,
                )
            for name, device in _iter_devices(document):
                _register_symbol(
                    file_symbols,
                    diagnostics,
                    file_id,
                    name,
                    "device",
                    device,
                )
            symbols[file_id] = file_symbols

        return cls(documents=dict(documents), symbols=symbols), diagnostics

    def lookup(self, file_id: Path, name: str) -> Optional[SymbolDef]:
        return self.symbols.get(file_id, {}).get(name)


def _register_symbol(
    file_symbols: Dict[str, SymbolDef],
    diagnostics: List[Diagnostic],
    file_id: Path,
    name: str,
    kind: SymbolKind,
    decl: ModuleDecl | DeviceDecl,
) -> None:
    if name in file_symbols:
        diagnostics.append(import_duplicate_symbol(name, _decl_loc(decl)))
        return
    file_symbols[name] = SymbolDef(
        file_id=file_id,
        name=name,
        kind=kind,
        decl=decl,
        loc=_decl_loc(decl),
    )


def _iter_modules(document: AsdlDocument) -> Iterable[Tuple[str, ModuleDecl]]:
    if document.modules is None:
        return []
    return document.modules.items()


def _iter_devices(document: AsdlDocument) -> Iterable[Tuple[str, DeviceDecl]]:
    if document.devices is None:
        return []
    return document.devices.items()


def _decl_loc(decl: ModuleDecl | DeviceDecl) -> Optional[Locatable]:
    return getattr(decl, "_loc", None)


__all__ = ["ProgramDB", "SymbolDef"]
