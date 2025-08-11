import json
from typing import Dict, List

from ..diagnostics import Diagnostic, DiagnosticSeverity


def diagnostics_to_jsonable(diagnostics: List[Diagnostic]) -> List[Dict[str, object]]:
    result: List[Dict[str, object]] = []
    for d in diagnostics:
        loc = d.location
        result.append(
            {
                "code": d.code,
                "severity": d.severity.name,
                "title": d.title,
                "message": d.details,
                "file": str(loc.file_path) if loc and loc.file_path else None,
                "line": loc.start_line if loc else None,
                "col": loc.start_col if loc else None,
                "suggestion": d.suggestion,
            }
        )
    return result


def has_error(diagnostics: List[Diagnostic]) -> bool:
    return any(d.severity == DiagnosticSeverity.ERROR for d in diagnostics)


def print_human_diagnostics(diagnostics: List[Diagnostic], echo) -> None:
    if not diagnostics:
        return
    for d in diagnostics:
        echo(str(d))
