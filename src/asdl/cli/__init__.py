from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Optional

import click

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


@cli.command("ir-dump")
@click.argument("input_file", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output file path.",
)
@click.option(
    "--ir",
    "ir_kind",
    type=click.Choice(["graphir", "ifir"], case_sensitive=False),
    default="ifir",
    show_default=True,
    help="IR to dump.",
)
@click.option(
    "--verify/--no-verify",
    default=True,
    show_default=True,
    help="Enable IR verification passes.",
)
@click.option(
    "--lib",
    "lib_roots",
    multiple=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Library search root (repeatable).",
)
def ir_dump(
    input_file: Path,
    output_path: Optional[Path],
    ir_kind: str,
    verify: bool,
    lib_roots: tuple[Path, ...],
) -> None:
    """Emit canonical GraphIR or IFIR text."""
    diagnostics: List[Diagnostic] = []
    try:
        from asdl.ir import dump_graphir, dump_ifir
        from asdl.ir.pipeline import (
            lower_import_graph_to_graphir,
            run_mvp_pipeline,
            verify_graphir_program,
        )
    except Exception as exc:  # pragma: no cover - defensive: missing optional deps
        diagnostics.append(
            _diagnostic(
                CLI_IMPORT_ERROR,
                f"Failed to load pipeline dependencies: {exc}",
            )
        )
        _emit_diagnostics(diagnostics)
        raise click.exceptions.Exit(1)

    ir_kind = ir_kind.lower()
    if ir_kind == "graphir":
        program, pipeline_diags = lower_import_graph_to_graphir(
            entry_file=input_file,
            lib_roots=lib_roots,
        )
        diagnostics.extend(pipeline_diags)
        if program is None or _has_error_diagnostics(diagnostics):
            _emit_diagnostics(diagnostics)
            raise click.exceptions.Exit(1)
        if verify:
            diagnostics.extend(verify_graphir_program(program))
            if _has_error_diagnostics(diagnostics):
                _emit_diagnostics(diagnostics)
                raise click.exceptions.Exit(1)
        output_text = dump_graphir(program)
    else:
        design, pipeline_diags = run_mvp_pipeline(
            entry_file=input_file,
            lib_roots=lib_roots,
            verify=verify,
        )
        diagnostics.extend(pipeline_diags)
        if design is None or _has_error_diagnostics(diagnostics):
            _emit_diagnostics(diagnostics)
            raise click.exceptions.Exit(1)
        output_text = dump_ifir(design)

    if output_path is None:
        click.echo(output_text, nl=False)
    else:
        try:
            output_path.write_text(output_text, encoding="utf-8")
        except OSError as exc:
            diagnostics.append(
                _diagnostic(
                    CLI_WRITE_ERROR,
                    f"Failed to write IR dump to '{output_path}': {exc}",
                )
            )
            _emit_diagnostics(diagnostics)
            raise click.exceptions.Exit(1)

    _emit_diagnostics(diagnostics)


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

    design, pipeline_diags = run_netlist_ir_pipeline(
        entry_file=input_file,
        lib_roots=lib_roots,
        verify=verify,
    )
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
