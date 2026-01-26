from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from click.testing import CliRunner

from asdl.cli import cli


def _write_backend_config(directory: Path, extension: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    config_path = directory / "backends.yaml"
    config_path.write_text(
        "\n".join(
            [
                "sim.ngspice:",
                f"  extension: \"{extension}\"",
                '  comment_prefix: "*"',
                "  templates:",
                '    __subckt_header__: ".subckt {name} {ports}"',
                '    __subckt_footer__: ".ends {name}"',
                '    __subckt_call__: "X{name} {ports} {ref}"',
                '    __netlist_header__: ""',
                '    __netlist_footer__: ".end"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path


def _write_library(path: Path, module_name: str, device_name: str) -> None:
    lines = [
        f"top: {module_name}",
        "modules:",
        f"  {module_name}:",
        "    instances:",
        f"      R1: {device_name}",
        "    nets:",
        "      $IN:",
        "        - R1.P",
        "      $OUT:",
        "        - R1.N",
        "devices:",
        f"  {device_name}:",
        "    ports: [P, N]",
        "    backends:",
        "      sim.ngspice:",
        '        template: "{name} {ports}"',
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_entry_with_imports(
    path: Path,
    imports: list[tuple[str, str, str]],
) -> None:
    lines = ["imports:"]
    for namespace, import_path, _module in imports:
        lines.append(f"  {namespace}: {import_path}")
    lines.extend(
        [
            "top: top",
            "modules:",
            "  top:",
            "    instances:",
        ]
    )
    for index, (namespace, _import_path, module_name) in enumerate(
        imports, start=1
    ):
        lines.append(f"      U{index}: {namespace}.{module_name}")
    lines.extend(
        [
            "    nets:",
            "      $IN:",
        ]
    )
    for index in range(1, len(imports) + 1):
        lines.append(f"        - U{index}.IN")
    lines.append("      $OUT:")
    for index in range(1, len(imports) + 1):
        lines.append(f"        - U{index}.OUT")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_cli_netlist_asdlrc_discovery_env_lib_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    project_root = tmp_path / "project"
    entry_dir = project_root / "src"
    entry_dir.mkdir(parents=True)

    lib_cli = project_root / "lib_cli"
    lib_rc = project_root / "lib_rc"
    lib_env = project_root / "lib_env"
    lib_cli.mkdir()
    lib_rc.mkdir()
    lib_env.mkdir()

    _write_library(lib_cli / "cli.asdl", "leaf_cli", "res_cli")
    _write_library(lib_rc / "rc.asdl", "leaf_rc", "res_rc")
    _write_library(lib_env / "env.asdl", "leaf_env", "res_env")

    entry_file = entry_dir / "entry.asdl"
    _write_entry_with_imports(
        entry_file,
        [
            ("cli", "cli.asdl", "leaf_cli"),
            ("rc", "rc.asdl", "leaf_rc"),
            ("env", "env.asdl", "leaf_env"),
        ],
    )

    backend_config = _write_backend_config(
        project_root / "configs", extension=".rcspice"
    )

    rc_path = project_root / ".asdlrc"
    rc_path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "lib_roots:",
                "  - lib_rc",
                f"backend_config: {backend_config.relative_to(project_root)}",
                "env:",
                "  ASDL_LIB_PATH: ${ASDLRC_DIR}/lib_env",
                "  EXISTING: rc_override",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("EXISTING", "keep")
    monkeypatch.delenv("ASDL_BACKEND_CONFIG", raising=False)
    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "netlist",
            str(entry_file),
            "--lib",
            str(lib_cli),
        ],
    )

    assert result.exit_code == 0
    output_path = entry_dir / "entry.rcspice"
    assert output_path.exists()
    assert os.environ["EXISTING"] == "keep"
    assert os.environ["ASDL_LIB_PATH"] == str(lib_env.absolute())


def test_cli_netlist_env_backend_overrides_rc(tmp_path: Path) -> None:
    entry_dir = tmp_path / "entry"
    entry_dir.mkdir()
    entry_file = entry_dir / "entry.asdl"

    rc_dir = tmp_path / "rc"
    lib_root = rc_dir / "lib"
    lib_root.mkdir(parents=True)
    _write_library(lib_root / "lib.asdl", "leaf_rc", "res_rc")
    _write_entry_with_imports(entry_file, [("lib", "lib.asdl", "leaf_rc")])

    rc_backend_config = _write_backend_config(rc_dir, extension=".rcspice")
    rc_path = rc_dir / ".asdlrc"
    rc_path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "lib_roots:",
                "  - lib",
                f"backend_config: {rc_backend_config.name}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    env_backend_config = _write_backend_config(
        tmp_path / "env", extension=".envspice"
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "netlist",
            str(entry_file),
            "--config",
            str(rc_path),
        ],
        env={"ASDL_BACKEND_CONFIG": str(env_backend_config)},
    )

    assert result.exit_code == 0
    output_path = entry_dir / "entry.envspice"
    assert output_path.exists()


def test_cli_visualizer_dump_uses_asdlrc_lib_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("xdsl")

    project_root = tmp_path / "project"
    entry_dir = project_root / "src"
    entry_dir.mkdir(parents=True)

    lib_root = project_root / "lib"
    lib_root.mkdir()
    _write_library(lib_root / "lib.asdl", "leaf_rc", "res_rc")

    entry_file = entry_dir / "entry.asdl"
    _write_entry_with_imports(entry_file, [("lib", "lib.asdl", "leaf_rc")])

    rc_path = project_root / ".asdlrc"
    rc_path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "lib_roots:",
                "  - lib",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("ASDL_LIB_PATH", raising=False)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "visualizer-dump",
            str(entry_file),
            "--list-modules",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema_version"] == 0
    module_names = {module["name"] for module in payload["modules"]}
    assert module_names == {"top"}
