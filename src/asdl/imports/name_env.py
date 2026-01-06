from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class NameEnv:
    file_id: Path
    bindings: Dict[str, Path]

    def resolve(self, namespace: str) -> Optional[Path]:
        return self.bindings.get(namespace)


__all__ = ["NameEnv"]
