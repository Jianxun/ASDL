from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, List, Optional, Tuple

Note = str


@dataclass(frozen=True)
class SourcePos:
    line: int
    col: int


@dataclass(frozen=True)
class SourceSpan:
    file: str
    start: Optional[SourcePos]
    end: Optional[SourcePos]
    byte_start: Optional[int] = None
    byte_end: Optional[int] = None

    def __post_init__(self) -> None:
        if (self.start is None) != (self.end is None):
            raise ValueError("start and end must be both set or both None")


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"

    def sort_rank(self) -> int:
        if self is Severity.FATAL:
            return 0
        if self is Severity.ERROR:
            return 1
        if self is Severity.WARNING:
            return 2
        return 3


@dataclass(frozen=True)
class Label:
    span: SourceSpan
    message: Optional[str] = None


@dataclass(frozen=True)
class FixIt:
    span: SourceSpan
    replacement: str
    message: Optional[str] = None


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: Severity
    message: str
    primary_span: Optional[SourceSpan] = None
    labels: Optional[List[Label]] = None
    notes: Optional[List[Note]] = None
    help: Optional[str] = None
    fixits: Optional[List[FixIt]] = None
    source: Optional[str] = None


def _file_sort_key(span: Optional[SourceSpan]) -> Tuple[int, str]:
    if span and span.file:
        return (0, span.file)
    return (1, "")


def _span_sort_key(span: Optional[SourceSpan]) -> Tuple[int, int, int]:
    if span and span.start:
        return (0, span.start.line, span.start.col)
    return (1, 0, 0)


def diagnostic_sort_key(diagnostic: Diagnostic) -> Tuple[object, ...]:
    span = diagnostic.primary_span
    file_key = _file_sort_key(span)
    span_key = _span_sort_key(span)
    return (
        file_key[0],
        file_key[1],
        span_key[0],
        span_key[1],
        span_key[2],
        diagnostic.severity.sort_rank(),
        diagnostic.code,
        diagnostic.message,
    )


def sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> List[Diagnostic]:
    return sorted(diagnostics, key=diagnostic_sort_key)


__all__ = [
    "Note",
    "SourcePos",
    "SourceSpan",
    "Severity",
    "Label",
    "FixIt",
    "Diagnostic",
    "diagnostic_sort_key",
    "sort_diagnostics",
]
