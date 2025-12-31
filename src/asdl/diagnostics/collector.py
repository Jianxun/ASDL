from __future__ import annotations

from typing import Iterable, Iterator, List

from .core import Diagnostic, sort_diagnostics


class DiagnosticCollector:
    def __init__(self) -> None:
        self._diagnostics: List[Diagnostic] = []

    def emit(self, diagnostic: Diagnostic) -> None:
        self._diagnostics.append(diagnostic)

    def extend(self, diagnostics: Iterable[Diagnostic]) -> None:
        self._diagnostics.extend(diagnostics)

    def clear(self) -> None:
        self._diagnostics.clear()

    def to_list(self, ordered: bool = True) -> List[Diagnostic]:
        if ordered:
            return sort_diagnostics(self._diagnostics)
        return list(self._diagnostics)

    def __iter__(self) -> Iterator[Diagnostic]:
        return iter(self._diagnostics)

    def __len__(self) -> int:
        return len(self._diagnostics)


__all__ = ["DiagnosticCollector"]
