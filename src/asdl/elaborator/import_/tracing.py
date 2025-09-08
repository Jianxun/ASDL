"""
Tracing helpers for the ASDL import system.

Centralizes logging of search paths, probe candidates, alias maps,
cycle stacks, and merge collisions with graceful fallback to DEBUG
when TRACE is unavailable.
"""

from typing import Iterable, Mapping

from ...logging_utils import get_logger


def log_search_paths(paths: Iterable) -> None:
    log = get_logger("elaborator.imports")
    msg = f"Search paths: {[str(p) for p in paths]}"
    try:
        log.trace(msg)
    except AttributeError:
        log.debug(msg)


def log_probe_candidates(relative_path: str, candidates: Iterable) -> None:
    log = get_logger("elaborator.imports")
    msg = f"Probe candidates for '{relative_path}': {[str(p) for p in candidates]}"
    try:
        log.trace(msg)
    except AttributeError:
        log.debug(msg)


def log_alias_map(file_path, alias_map: Mapping[str, object]) -> None:
    log = get_logger("elaborator.imports")
    formatted = {k: (str(v) if v is not None else None) for k, v in alias_map.items()}
    msg = f"Alias map for {file_path}: {formatted}"
    try:
        log.trace(msg)
    except AttributeError:
        log.debug(msg)


def log_merge_conflict(module_name: str, policy: str) -> None:
    log = get_logger("elaborator.imports")
    msg = f"Merge conflict on module '{module_name}' (policy={policy})"
    try:
        log.trace(msg)
    except AttributeError:
        log.debug(msg)


