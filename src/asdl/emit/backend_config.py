"""Backend configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from asdl.diagnostics import Diagnostic, Severity, format_code

MISSING_BACKEND = format_code("EMIT", 4)

# Required system devices (backends MUST define these)
REQUIRED_SYSTEM_DEVICES = {
    "__subckt_header__",
    "__subckt_footer__",
    "__subckt_call__",
    "__netlist_header__",
    "__netlist_footer__",
}

# Optional system devices (backends MAY define these)
OPTIONAL_SYSTEM_DEVICES: set[str] = set()


@dataclass(frozen=True)
class SystemDeviceTemplate:
    """A single system device template definition."""

    template: str


@dataclass(frozen=True)
class BackendConfig:
    """Backend configuration loaded from backends.yaml."""

    name: str
    extension: str
    comment_prefix: str
    templates: Dict[str, SystemDeviceTemplate]


def load_backend_config(
    backend_name: str, config_path: Optional[Path] = None
) -> BackendConfig:
    """Load backend configuration from YAML file.

    Args:
        backend_name: Name of the backend to load (e.g., "sim.ngspice")
        config_path: Path to backend config file. If None, uses ASDL_BACKEND_CONFIG
                     env var or defaults to config/backends.yaml

    Returns:
        BackendConfig object

    Raises:
        FileNotFoundError: If config file doesn't exist
        KeyError: If backend not found in config file
        yaml.YAMLError: If YAML is malformed
    """
    if config_path is None:
        env_path = os.environ.get("ASDL_BACKEND_CONFIG")
        if env_path:
            config_path = Path(env_path)
        else:
            config_path = Path("config/backends.yaml")

    if not config_path.exists():
        raise FileNotFoundError(f"Backend config file not found: {config_path}")

    with open(config_path, "r") as f:
        data = yaml.safe_load(f)

    if backend_name not in data:
        raise KeyError(
            f"Backend '{backend_name}' not found in {config_path}"
        )

    backend_data = data[backend_name]
    if "extension" not in backend_data:
        raise KeyError(f"Backend '{backend_name}' missing required key: extension")
    if "comment_prefix" not in backend_data:
        raise KeyError(
            f"Backend '{backend_name}' missing required key: comment_prefix"
        )
    if "templates" not in backend_data:
        raise KeyError(f"Backend '{backend_name}' missing required key: templates")

    extension = backend_data["extension"]
    comment_prefix = backend_data["comment_prefix"]
    templates_raw = backend_data["templates"]

    if not isinstance(templates_raw, dict):
        raise TypeError(
            f"Backend '{backend_name}' templates must be a mapping of name to template"
        )

    templates = {
        name: SystemDeviceTemplate(template=template)
        for name, template in templates_raw.items()
    }

    return BackendConfig(
        name=backend_name,
        extension=extension,
        comment_prefix=comment_prefix,
        templates=templates,
    )


def validate_system_devices(config: BackendConfig) -> List[Diagnostic]:
    """Validate that all required system devices are present.

    Args:
        config: Backend configuration to validate

    Returns:
        List of diagnostics (errors if required devices missing)
    """
    diagnostics: List[Diagnostic] = []
    missing = REQUIRED_SYSTEM_DEVICES - set(config.templates.keys())

    if missing:
        missing_list = ", ".join(sorted(missing))
        diagnostics.append(
            Diagnostic(
                code=MISSING_BACKEND,
                severity=Severity.ERROR,
                message=(
                    f"Backend '{config.name}' is missing required system devices: "
                    f"{missing_list}"
                ),
                source="emit",
            )
        )

    return diagnostics


__all__ = [
    "BackendConfig",
    "SystemDeviceTemplate",
    "REQUIRED_SYSTEM_DEVICES",
    "OPTIONAL_SYSTEM_DEVICES",
    "load_backend_config",
    "validate_system_devices",
]
