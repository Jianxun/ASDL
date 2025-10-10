from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, List

import click

from ..logging_utils import get_logger, configure_logging
from ..parser import ASDLParser
from ..diagnostics import Diagnostic
from .helpers import diagnostics_to_jsonable, has_error, print_human_diagnostics
from ..ir import build_textual_ir, register_asdl_dialect
from ..ir.converter import asdl_ast_to_xdsl_module, print_xdsl_module


@click.command("ir-dump", help="Parse → (import flatten optional) → AST→IR and print textual IR")
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--verify", is_flag=True, help="Run basic verifications before printing")
@click.option("--run-pass", "run_passes", multiple=True, help="Passes to run (reserved; no-ops in Phase 0)")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON to stdout (diagnostics)")
@click.option("--engine", type=click.Choice(["textual", "xdsl"]), default="textual", show_default=True,
              help="Select IR engine: minimal textual (default) or xDSL dialect")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logs (INFO level)")
def ir_dump_cmd(input: Path, verify: bool, run_passes: tuple[str, ...], json_output: bool, engine: str, verbose: bool) -> None:
    exit_code = 0
    diagnostics: List[Diagnostic] = []

    try:
        configure_logging(verbose=verbose)
        log = get_logger("cli")
        log.debug("Starting ir-dump")

        parser = ASDLParser(preserve_unknown=True)
        asdl_file, parse_diags = parser.parse_file(str(input))
        diagnostics.extend(parse_diags)
        if has_error(parse_diags):
            raise click.ClickException("Failed to parse ASDL file.")
        if asdl_file is None:
            raise click.ClickException("No AST produced by parser.")

        # Phase 0: no-op passes; placeholder for future run_pass execution
        if verify:
            # Minimal verification placeholder: ensure at least one module exists
            if not asdl_file.modules:
                raise click.ClickException("Verify failed: no modules in AST.")

        if engine == "textual":
            textual = build_textual_ir(asdl_file)
            click.echo(textual)
        else:
            # xDSL engine
            mlctx, mod = asdl_ast_to_xdsl_module(asdl_file)
            textual = print_xdsl_module(mlctx, mod)
            click.echo(textual)

    except click.ClickException as e:
        exit_code = 1
        if json_output:
            payload = {
                "error": str(e),
                "diagnostics": diagnostics_to_jsonable(diagnostics),
            }
            click.echo(click.style(str(payload), fg="red"))
        else:
            print_human_diagnostics(diagnostics, click.echo)
            click.echo(f"CLI error: {e}")
    finally:
        sys.exit(exit_code)


