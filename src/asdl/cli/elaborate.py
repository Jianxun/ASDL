import json
import sys
from pathlib import Path
from typing import Optional, List

import click
from ..logging_utils import get_logger, configure_logging

from ..parser import ASDLParser
from ..elaborator import Elaborator
from ..diagnostics import Diagnostic
from .. import serialization as asdl_serialization
from .helpers import diagnostics_to_jsonable, has_error, print_human_diagnostics


@click.command("elaborate", help="Parse → elaborate; emit elaborated ASDL to file")
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path), help="Output file (default: input with .elab.{yaml|json})")
@click.option("--format", "fmt", type=click.Choice(["yaml", "json"], case_sensitive=False), default="yaml", show_default=True)
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON to stdout")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logs (INFO level)")
@click.option("--top", type=str, help="Override top module")
@click.pass_context
def elaborate_cmd(ctx: click.Context, input: Path, output: Optional[Path], fmt: str, json_output: bool, verbose: bool, top: Optional[str]) -> None:
    exit_code = 0
    diagnostics: List[Diagnostic] = []
    artifact_path: Optional[Path] = None

    try:
        # Reconfigure logging to include verbose flag combined with base options
        configure_logging(
            verbose=verbose,
            debug=ctx.obj.get("debug", False),
            trace=ctx.obj.get("trace", False),
            log_file=ctx.obj.get("log_file"),
            log_json=ctx.obj.get("log_json"),
        )
        log = get_logger("cli")
        log.info("[parse] reading input…")
        elaborator = Elaborator()
        log.info("[imports] resolving…")
        elaborated_file, elab_diags = elaborator.elaborate_with_imports(input, top=top)
        diagnostics.extend(elab_diags)
        if elaborated_file is None:
            exit_code = 1
        else:
            if output is None:
                suffix = ".elab.yaml" if fmt.lower() == "yaml" else ".elab.json"
                artifact_path = input.with_suffix(suffix)
            else:
                artifact_path = output
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            if fmt.lower() == "yaml":
                asdl_serialization.save_asdl_to_yaml_file(elaborated_file, str(artifact_path))
            else:
                as_json = asdl_serialization.asdl_to_json_string(elaborated_file)
                artifact_path.write_text(as_json, encoding="utf-8")

        exit_code = 1 if has_error(diagnostics) else exit_code

        if json_output:
            payload = {
                "ok": exit_code == 0,
                "stage": "elaborate",
                "artifacts": {"elaborated": str(artifact_path) if artifact_path else None},
                "diagnostics": diagnostics_to_jsonable(diagnostics),
            }
            click.echo(json.dumps(payload, indent=2))
        else:
            print_human_diagnostics(diagnostics, click.echo)
            if artifact_path:
                log.info(f"elaborated written to: {artifact_path}")

    except click.ClickException as e:
        exit_code = 2
        msg = {"ok": False, "stage": "elaborate", "diagnostics": [{"code": "CLI", "severity": "ERROR", "title": "CLI error", "message": str(e)}]}
        click.echo(json.dumps(msg, indent=2) if json_output else f"CLI error: {e}")
    except Exception as e:
        exit_code = 3
        msg = {"ok": False, "stage": "elaborate", "diagnostics": [{"code": "INTERNAL", "severity": "ERROR", "title": "Internal error", "message": str(e)}]}
        click.echo(json.dumps(msg, indent=2) if json_output else f"Unexpected error: {e}")

    sys.exit(exit_code)
