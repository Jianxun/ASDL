from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

import click

from asdl.ast import parse_file
from asdl.diagnostics import Diagnostic, Severity, format_code, render_text

NO_SPAN_NOTE = "No source span available."

CLI_IMPORT_ERROR = format_code("TOOL", 1)
CLI_WRITE_ERROR = format_code("TOOL", 2)


@click.group()
def cli() -> None:
    """ASDL compiler (asdlc)."""


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
    "--top-as-subckt",
    is_flag=True,
    default=False,
    help="Emit top module as a .subckt block.",
)
def netlist(
    input_file: Path,
    output_path: Optional[Path],
    verify: bool,
    top_as_subckt: bool,
) -> None:
    """Generate an ngspice netlist from ASDL."""
    diagnostics: List[Diagnostic] = []

    document, parse_diags = parse_file(str(input_file))
    diagnostics.extend(parse_diags)
    if document is None:
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    try:
        from asdl.emit.ngspice import emit_ngspice
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

    netlist_text, emit_diags = emit_ngspice(design, top_as_subckt=top_as_subckt)
    diagnostics.extend(emit_diags)
    if netlist_text is None or _has_error_diagnostics(diagnostics):
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    if output_path is None:
        output_path = input_file.with_suffix(".spice")

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
