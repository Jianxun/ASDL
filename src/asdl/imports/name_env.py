from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class NameEnv:
    file_id: str
    namespaces: Dict[str, str]

    def resolve(self, namespace: str) -> Optional[str]:
        return self.namespaces.get(namespace)


__all__ = ["NameEnv"]
