from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .program_db import ProgramDB


@dataclass(frozen=True)
class NameEnv:
    file_id: Path
    bindings: Dict[str, Path]

    def resolve(self, namespace: str) -> Optional[Path]:
        return self.bindings.get(namespace)

    def has_local_symbol(self, program_db: "ProgramDB", name: str) -> bool:
        return program_db.lookup(self.file_id, name) is not None


__all__ = ["NameEnv"]
