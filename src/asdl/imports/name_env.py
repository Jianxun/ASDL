from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .program_db import ProgramDB, SymbolDef


@dataclass(frozen=True)
class NameEnv:
    file_id: Path
    bindings: Dict[str, Path]

    def resolve(self, namespace: str) -> Optional[Path]:
        return self.bindings.get(namespace)

    def resolve_local(self, name: str, program_db: ProgramDB) -> Optional[SymbolDef]:
        return program_db.lookup(self.file_id, name)


__all__ = ["NameEnv"]
