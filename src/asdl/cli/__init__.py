from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

import click

from asdl.ast import parse_file
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
        from asdl.schema import write_schema_artifacts
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


@cli.command("netlist")
@click.argument("input_file", type=click.Path(dir_okay=False, path_type=Path))
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
    "--top-as-subckt",
    is_flag=True,
    default=False,
    help="Emit top module as a .subckt block.",
)
def netlist(
    input_file: Path,
    output_path: Optional[Path],
    verify: bool,
    backend: str,
    top_as_subckt: bool,
) -> None:
    """Generate a netlist from ASDL.

    Supported placeholders: {name}, {ports} (optional). {params} is deprecated.
    Library search path: ASDL_LIB_PATH (PATH-style list).
    """
    diagnostics: List[Diagnostic] = []

    document, parse_diags = parse_file(str(input_file))
    diagnostics.extend(parse_diags)
    if document is None:
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    try:
        from asdl.emit.netlist import emit_netlist, load_backend
        from asdl.ir.pipeline import run_mvp_pipeline
    except Exception as exc:  # pragma: no cover - defensive: missing optional deps
        diagnostics.append(
            _diagnostic(
                CLI_IMPORT_ERROR,
                f"Failed to load pipeline dependencies: {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    design, pipeline_diags = run_mvp_pipeline(document, verify=verify)
    diagnostics.extend(pipeline_diags)
    if design is None or _has_error_diagnostics(diagnostics):
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    backend_config, backend_diags = load_backend(backend)
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
