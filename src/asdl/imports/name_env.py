from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from asdl.diagnostics import Diagnostic

from .diagnostics import duplicate_namespace


@dataclass
class NameEnv:
    file_id: str
    namespaces: Dict[str, str] = field(default_factory=dict)

    def bind(self, namespace: str, file_id: str) -> Optional[Diagnostic]:
        if namespace in self.namespaces:
            return duplicate_namespace(namespace)
        self.namespaces[namespace] = file_id
        return None


__all__ = ["NameEnv"]
