"""Project .asdlrc discovery and parsing utilities."""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
from pathlib import Path
from typing import Mapping, Optional

import yaml

ASDLRC_FILENAME = ".asdlrc"
ASDLRC_SCHEMA_VERSION = 1
_TOKEN_PATTERN = re.compile(r"\$\{([^}]+)\}")
_MAX_EXPANSION_PASSES = 10


@dataclass(frozen=True)
class AsdlrcConfig:
    """Parsed .asdlrc configuration."""

    rc_path: Path
    lib_roots: list[Path]
    backend_config: Optional[Path]
    env: dict[str, str]


def discover_asdlrc(entry_file: Path) -> Optional[Path]:
    """Discover a .asdlrc by walking parent directories from an entry file.

    Args:
        entry_file: Entry file to anchor discovery.

    Returns:
        Path to the first .asdlrc found (nearest ancestor), or None if missing.
    """
    entry_path = Path(entry_file).absolute()
    start_dir = entry_path.parent
    for current in [start_dir, *start_dir.parents]:
        candidate = current / ASDLRC_FILENAME
        if candidate.is_file():
            return candidate.absolute()
    return None


def load_asdlrc(
    entry_file: Path, *, config_path: Optional[Path] = None
) -> Optional[AsdlrcConfig]:
    """Load an .asdlrc discovered from an entry file or explicit path.

    Args:
        entry_file: Entry file to anchor discovery when config_path is None.
        config_path: Optional explicit rc path (overrides discovery).

    Returns:
        Parsed AsdlrcConfig or None when no rc file is found.
    """
    if config_path is not None:
        rc_path = Path(config_path).absolute()
    else:
        rc_path = discover_asdlrc(entry_file)
    if rc_path is None:
        return None
    return parse_asdlrc(rc_path)


def parse_asdlrc(
    rc_path: Path, *, environ: Optional[Mapping[str, str]] = None
) -> AsdlrcConfig:
    """Parse a .asdlrc YAML file into an AsdlrcConfig.

    Args:
        rc_path: Path to the rc file.
        environ: Optional environment mapping for interpolation (defaults to
            os.environ).

    Returns:
        Parsed AsdlrcConfig with interpolated values.

    Raises:
        FileNotFoundError: If rc_path does not exist.
        TypeError: If the rc schema has invalid types.
        ValueError: If the schema_version is missing or unsupported.
        yaml.YAMLError: If YAML parsing fails.
    """
    rc_path = Path(rc_path)
    if not rc_path.exists():
        raise FileNotFoundError(f".asdlrc not found: {rc_path}")

    with rc_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise TypeError(".asdlrc must be a YAML mapping")

    schema_version = data.get("schema_version")
    if schema_version != ASDLRC_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported .asdlrc schema_version; expected 1."
        )

    raw_env = _parse_env(data.get("env"))
    rc_dir = rc_path.absolute().parent
    base_env = dict(os.environ if environ is None else environ)
    base_env["ASDLRC_DIR"] = str(rc_dir)

    expanded_env, effective_env = _expand_env(raw_env, base_env)

    raw_lib_roots = _parse_lib_roots(data.get("lib_roots"))
    lib_roots = [
        _resolve_rc_path(
            _expand_tokens(root, effective_env),
            rc_dir,
        )
        for root in raw_lib_roots
    ]

    backend_config_raw = data.get("backend_config")
    backend_config = None
    if backend_config_raw is not None:
        if not isinstance(backend_config_raw, str):
            raise TypeError("backend_config must be a string path")
        expanded_backend = _expand_tokens(
            backend_config_raw,
            effective_env,
        )
        backend_config = _resolve_rc_path(expanded_backend, rc_dir)

    return AsdlrcConfig(
        rc_path=rc_path.absolute(),
        lib_roots=lib_roots,
        backend_config=backend_config,
        env=expanded_env,
    )


def _parse_env(raw_env: object) -> dict[str, str]:
    if raw_env is None:
        return {}
    if not isinstance(raw_env, dict):
        raise TypeError("env must be a mapping of string keys to string values")
    parsed: dict[str, str] = {}
    for key, value in raw_env.items():
        if not isinstance(key, str):
            raise TypeError("env keys must be strings")
        if not isinstance(value, str):
            raise TypeError("env values must be strings")
        parsed[key] = value
    return parsed


def _parse_lib_roots(raw_roots: object) -> list[str]:
    if raw_roots is None:
        return []
    if not isinstance(raw_roots, list):
        raise TypeError("lib_roots must be a list of string paths")
    roots: list[str] = []
    for root in raw_roots:
        if not isinstance(root, str):
            raise TypeError("lib_roots entries must be strings")
        roots.append(root)
    return roots


def _expand_env(
    raw_env: Mapping[str, str],
    base_env: Mapping[str, str],
) -> tuple[dict[str, str], dict[str, str]]:
    expanded_env: dict[str, str] = {}
    effective_env = dict(base_env)
    for key, value in raw_env.items():
        if key not in effective_env:
            effective_env[key] = value

    for _ in range(_MAX_EXPANSION_PASSES):
        changed = False
        for key, raw_value in raw_env.items():
            expanded_value = _expand_tokens(raw_value, effective_env)
            if expanded_env.get(key) != expanded_value:
                expanded_env[key] = expanded_value
                changed = True
            if key not in base_env:
                effective_env[key] = expanded_value
        if not changed:
            break

    return expanded_env, effective_env


def _expand_tokens(value: str, env: Mapping[str, str]) -> str:
    expanded = value
    for _ in range(_MAX_EXPANSION_PASSES):
        next_value = _TOKEN_PATTERN.sub(
            lambda match: env.get(match.group(1), match.group(0)),
            expanded,
        )
        if next_value == expanded:
            return expanded
        expanded = next_value
    return expanded


def _resolve_rc_path(value: str, rc_dir: Path) -> Path:
    expanded = os.path.expanduser(value)
    if expanded.strip() == "":
        raise ValueError("Path entry resolved to an empty string")
    path = Path(expanded)
    if not path.is_absolute():
        path = rc_dir / path
    return path.absolute()


__all__ = [
    "ASDLRC_FILENAME",
    "ASDLRC_SCHEMA_VERSION",
    "AsdlrcConfig",
    "discover_asdlrc",
    "load_asdlrc",
    "parse_asdlrc",
]
