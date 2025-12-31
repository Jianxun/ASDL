from __future__ import annotations

from typing import Iterable

ALLOWED_DOMAINS = ("PARSE", "AST", "IR", "PASS", "EMIT", "LINT", "TOOL")


def format_code(domain: str, number: int) -> str:
    if domain not in ALLOWED_DOMAINS:
        raise ValueError(f"Unknown diagnostic domain '{domain}'")
    if number < 0 or number > 999:
        raise ValueError("Diagnostic number must be between 0 and 999")
    return f"{domain}-{number:03d}"


def is_valid_code(code: str) -> bool:
    if "-" not in code:
        return False
    domain, number = code.split("-", 1)
    if domain not in ALLOWED_DOMAINS:
        return False
    if len(number) != 3 or not number.isdigit():
        return False
    return True


__all__ = ["ALLOWED_DOMAINS", "format_code", "is_valid_code"]
