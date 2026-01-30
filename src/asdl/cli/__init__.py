from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable, List, Optional

import click
import yaml

from asdl.diagnostics import Diagnostic, Severity, format_code, render_text

NO_SPAN_NOTE = "No source span available."

CLI_IMPORT_ERROR = format_code("TOOL", 1)
CLI_WRITE_ERROR = format_code("TOOL", 2)
CLI_SCHEMA_ERROR = format_code("TOOL", 3)


@click.group()
def cli() -> None:
    """ASDL compiler (asdlc)."""


@cli.command("schema")
@click.option(
    "--out",
    "output_dir",
    type=click.Path(file_okay=False, path_type=Path),
    help="Output directory (defaults to the current working directory).",
)
def schema(output_dir: Optional[Path]) -> None:
    """Generate ASDL schema artifacts."""
    diagnostics: List[Diagnostic] = []
    if output_dir is None:
        output_dir = Path.cwd()

    try:
        from asdl.ast.schema import write_schema_artifacts
    except Exception as exc:  # pragma: no cover - defensive: missing optional deps
        diagnostics.append(
            _diagnostic(
                CLI_IMPORT_ERROR,
                f"Failed to load schema generator: {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    try:
        json_path, txt_path = write_schema_artifacts(output_dir)
    except OSError as exc:
        diagnostics.append(
            _diagnostic(
                CLI_WRITE_ERROR,
                f"Failed to write schema to '{output_dir}': {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)
    except Exception as exc:
        diagnostics.append(
            _diagnostic(
                CLI_SCHEMA_ERROR,
                f"Failed to generate schema: {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    click.echo(f"Wrote: {json_path}")
    click.echo(f"Wrote: {txt_path}")


@cli.command("patterned-graph-dump")
@click.argument("input_file", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path.",
)
@click.option(
    "--compact",
    is_flag=True,
    default=False,
    help="Emit compact JSON output.",
)
def patterned_graph_dump(
    input_file: Path,
    output_path: Optional[Path],
    compact: bool,
) -> None:
    """Emit PatternedGraph JSON."""
    diagnostics: List[Diagnostic] = []
    try:
        from asdl.core import dump_patterned_graph, patterned_graph_to_jsonable
        from asdl.core.pipeline import run_patterned_graph_pipeline
    except Exception as exc:  # pragma: no cover - defensive: missing optional deps
        diagnostics.append(
            _diagnostic(
                CLI_IMPORT_ERROR,
                f"Failed to load PatternedGraph pipeline dependencies: {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    graph, pipeline_diags = run_patterned_graph_pipeline(entry_file=input_file)
    diagnostics.extend(pipeline_diags)
    if graph is None or _has_error_diagnostics(diagnostics):
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    if compact:
        output_text = json.dumps(
            patterned_graph_to_jsonable(graph),
            sort_keys=True,
            separators=(",", ":"),
        )
    else:
        output_text = dump_patterned_graph(graph)

    if output_path is None:
        click.echo(output_text, nl=False)
    else:
        try:
            output_path.write_text(output_text, encoding="utf-8")
        except OSError as exc:
            diagnostics.append(
                _diagnostic(
                    CLI_WRITE_ERROR,
                    f"Failed to write PatternedGraph dump to '{output_path}': {exc}",
                )
            )
            _emit_diagnostics(diagnostics)
            raise click.exceptions.Exit(1)

    _emit_diagnostics(diagnostics)


@cli.command("visualizer-dump")
@click.argument(
    "input_files",
    type=click.Path(dir_okay=False, path_type=Path),
    nargs=-1,
)
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Explicit .asdlrc path (overrides discovery).",
)
@click.option(
    "--module",
    "module_name",
    help="Module name to dump.",
)
@click.option(
    "--list-modules",
    is_flag=True,
    default=False,
    help="List entry-file modules and exit.",
)
@click.option(
    "--compact",
    is_flag=True,
    default=False,
    help="Emit compact JSON output.",
)
def visualizer_dump(
    input_files: tuple[Path, ...],
    config_path: Optional[Path],
    module_name: Optional[str],
    list_modules: bool,
    compact: bool,
) -> None:
    """Emit minimal JSON for the visualizer."""
    diagnostics: List[Diagnostic] = []
    try:
        from asdl.core import (
            visualizer_dump_to_jsonable,
            visualizer_module_list_to_jsonable,
        )
        from asdl.core.pipeline import list_entry_modules, run_patterned_graph_pipeline
    except Exception as exc:  # pragma: no cover - defensive: missing optional deps
        diagnostics.append(
            _diagnostic(
                CLI_IMPORT_ERROR,
                f"Failed to load visualizer dump dependencies: {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    if module_name and list_modules:
        diagnostics.append(
            _diagnostic(
                CLI_SCHEMA_ERROR,
                "Use either --module or --list-modules, not both.",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    if not input_files:
        diagnostics.append(
            _diagnostic(
                CLI_SCHEMA_ERROR,
                "Provide at least one input file.",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    if len(input_files) > 1 and not list_modules:
        diagnostics.append(
            _diagnostic(
                CLI_SCHEMA_ERROR,
                "visualizer-dump accepts multiple inputs only with --list-modules.",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    payloads: list[dict] = []
    for input_file in input_files:
        lib_roots, _backend_config = _resolve_rc_settings(
            input_file, config_path, (), diagnostics
        )
        graph, pipeline_diags = run_patterned_graph_pipeline(
            entry_file=input_file, lib_roots=lib_roots
        )
        diagnostics.extend(pipeline_diags)
        if graph is None or _has_error_diagnostics(diagnostics):
            _emit_diagnostics(diagnostics)
            raise click.exceptions.Exit(1)

        entry_modules = list_entry_modules(graph, input_file)
        if list_modules:
            if not entry_modules:
                diagnostics.append(
                    _diagnostic(
                        CLI_SCHEMA_ERROR,
                        "Entry file contains no modules to list.",
                    )
                )
                _emit_diagnostics(diagnostics)
                raise click.exceptions.Exit(1)
            payloads.append(visualizer_module_list_to_jsonable(entry_modules))
            continue

        if not entry_modules:
            diagnostics.append(
                _diagnostic(
                    CLI_SCHEMA_ERROR,
                    "Entry file contains no modules to dump.",
                )
            )
            _emit_diagnostics(diagnostics)
            raise click.exceptions.Exit(1)

        selected_module = None
        if module_name:
            matches = [module for module in entry_modules if module.name == module_name]
            if len(matches) == 1:
                selected_module = matches[0]
            elif not matches:
                diagnostics.append(
                    _diagnostic(
                        CLI_SCHEMA_ERROR,
                        f"Module '{module_name}' not found in entry file.",
                    )
                )
            else:
                diagnostics.append(
                    _diagnostic(
                        CLI_SCHEMA_ERROR,
                        f"Multiple modules named '{module_name}' found in entry file.",
                    )
                )
        else:
            if len(entry_modules) == 1:
                selected_module = entry_modules[0]
            else:
                diagnostics.append(
                    _diagnostic(
                        CLI_SCHEMA_ERROR,
                        "Multiple modules found; use --module or --list-modules.",
                    )
                )

        if selected_module is None or _has_error_diagnostics(diagnostics):
            _emit_diagnostics(diagnostics)
            raise click.exceptions.Exit(1)
        payloads.append(
            visualizer_dump_to_jsonable(
                graph,
                selected_module.module_id,
                diagnostics=diagnostics,
            )
        )

    payload: object = payloads[0] if len(payloads) == 1 else payloads

    if compact:
        output_text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    else:
        output_text = json.dumps(payload, sort_keys=True, indent=2)

    click.echo(output_text, nl=False)
    _emit_diagnostics(diagnostics)


@cli.command("netlist")
@click.argument("input_file", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Explicit .asdlrc path (overrides discovery).",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path.",
)
@click.option(
    "--verify/--no-verify",
    default=True,
    show_default=True,
    help="Enable IR verification passes.",
)
@click.option(
    "--backend",
    default="sim.ngspice",
    show_default=True,
    help="Backend name from the backend config.",
)
@click.option(
    "--lib",
    "lib_roots",
    multiple=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Library search root (repeatable).",
)
@click.option(
    "--top-as-subckt",
    is_flag=True,
    default=False,
    help="Emit top module as a .subckt block.",
)
def netlist(
    input_file: Path,
    config_path: Optional[Path],
    output_path: Optional[Path],
    verify: bool,
    backend: str,
    lib_roots: tuple[Path, ...],
    top_as_subckt: bool,
) -> None:
    """Generate a netlist from ASDL.

    Supported placeholders: {name}, {ports} (optional). {params} is deprecated.
    Library search path: repeatable --lib roots, then ASDL_LIB_PATH (PATH-style list).
    """
    diagnostics: List[Diagnostic] = []

    try:
        from asdl.emit.netlist import emit_netlist, load_backend
        from asdl.lowering import run_netlist_ir_pipeline
    except Exception as exc:  # pragma: no cover - defensive: missing optional deps
        diagnostics.append(
            _diagnostic(
                CLI_IMPORT_ERROR,
                f"Failed to load pipeline dependencies: {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    resolved_lib_roots, backend_config_path = _resolve_rc_settings(
        input_file, config_path, lib_roots, diagnostics
    )
    design, pipeline_diags = run_netlist_ir_pipeline(
        entry_file=input_file,
        lib_roots=resolved_lib_roots,
        verify=verify,
    )
    diagnostics.extend(pipeline_diags)
    if design is None or _has_error_diagnostics(diagnostics):
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    backend_config, backend_diags = load_backend(
        backend, backend_config_path=backend_config_path
    )
    diagnostics.extend(backend_diags)
    if backend_config is None or _has_error_diagnostics(diagnostics):
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    netlist_text, emit_diags = emit_netlist(
        design,
        top_as_subckt=top_as_subckt,
        backend_name=backend,
        backend_config=backend_config,
    )
    diagnostics.extend(emit_diags)
    if netlist_text is None or _has_error_diagnostics(diagnostics):
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    if output_path is None:
        output_path = input_file.with_suffix(backend_config.extension)

    try:
        output_path.write_text(netlist_text, encoding="utf-8")
    except OSError as exc:
        diagnostics.append(
            _diagnostic(
                CLI_WRITE_ERROR,
                f"Failed to write netlist to '{output_path}': {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    _emit_diagnostics(diagnostics)


def _emit_diagnostics(diagnostics: Iterable[Diagnostic]) -> None:
    rendered = render_text(diagnostics)
    if rendered:
        click.echo(rendered, err=True)


def _has_error_diagnostics(diagnostics: Iterable[Diagnostic]) -> bool:
    return any(
        diagnostic.severity in (Severity.ERROR, Severity.FATAL)
        for diagnostic in diagnostics
    )


def _resolve_rc_settings(
    entry_file: Path,
    config_path: Optional[Path],
    cli_lib_roots: Iterable[Path],
    diagnostics: List[Diagnostic],
) -> tuple[list[Path], Optional[Path]]:
    """Resolve rc-derived settings for a CLI entry file.

    Args:
        entry_file: Entry file path used for rc discovery.
        config_path: Optional explicit rc path (overrides discovery).
        cli_lib_roots: Library roots supplied on the CLI (first in precedence).
        diagnostics: Diagnostics list to append rc load failures.

    Returns:
        Tuple of (combined lib roots, backend config path override).
    """
    try:
        from asdl.cli.config import load_asdlrc
    except Exception as exc:  # pragma: no cover - defensive: missing optional deps
        diagnostics.append(
            _diagnostic(
                CLI_IMPORT_ERROR,
                f"Failed to load .asdlrc support: {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    try:
        rc_config = load_asdlrc(entry_file, config_path=config_path)
    except (FileNotFoundError, TypeError, ValueError, yaml.YAMLError) as exc:
        diagnostics.append(
            _diagnostic(
                CLI_SCHEMA_ERROR,
                f"Failed to load .asdlrc: {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    combined_roots = list(cli_lib_roots)
    backend_config_path: Optional[Path] = None
    if rc_config is None:
        return combined_roots, backend_config_path

    _merge_rc_env(rc_config.env)
    combined_roots.extend(rc_config.lib_roots)

    if rc_config.backend_config and os.environ.get("ASDL_BACKEND_CONFIG") is None:
        backend_config_path = rc_config.backend_config

    return combined_roots, backend_config_path


def _merge_rc_env(env: dict[str, str]) -> None:
    """Merge rc env entries into os.environ without overriding existing keys."""
    for key, value in env.items():
        os.environ.setdefault(key, value)


def _diagnostic(code: str, message: str) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=Severity.ERROR,
        message=message,
        primary_span=None,
        notes=[NO_SPAN_NOTE],
        source="cli",
    )


__all__ = ["cli"]
