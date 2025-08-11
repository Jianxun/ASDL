import json
import sys
from pathlib import Path
from typing import Optional, List

import click

from ..parser import ASDLParser
from ..elaborator import Elaborator
from ..validator import ASDLValidator
from ..diagnostics import Diagnostic
from .helpers import diagnostics_to_jsonable, has_error, print_human_diagnostics


@click.command("validate", help="Parse → (elaborate) → validate; no SPICE output")
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON to stdout")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logs")
@click.option("--top", type=str, help="Override top module")
def validate_cmd(input: Path, json_output: bool, verbose: bool, top: Optional[str]) -> None:
    exit_code = 0
    diagnostics: List[Diagnostic] = []

    try:
        if verbose:
            click.echo("[parse] reading input…")
        parser = ASDLParser()
        asdl_file, parse_diags = parser.parse_file(str(input))
        diagnostics.extend(parse_diags)

        if asdl_file is None:
            payload = {
                "ok": False,
                "stage": "validate",
                "diagnostics": diagnostics_to_jsonable(diagnostics),
                "artifacts": {},
            }
            if json_output:
                click.echo(json.dumps(payload, indent=2))
            else:
                print_human_diagnostics(diagnostics, click.echo)
            sys.exit(1)

        if top:
            asdl_file.file_info.top_module = top

        if verbose:
            click.echo("[elaborate] expanding patterns…")
        elaborator = Elaborator()
        elaborated_file, elab_diags = elaborator.elaborate(asdl_file)
        diagnostics.extend(elab_diags)
        if elaborated_file is None:
            exit_code = 1
        else:
            if verbose:
                click.echo("[validate] running structural checks…")
            validator = ASDLValidator()
            for module_name, module in (elaborated_file.modules or {}).items():
                diagnostics.extend(validator.validate_net_declarations(module, module_name))
                if module.instances:
                    for inst_id, inst in module.instances.items():
                        if inst.model in elaborated_file.modules:
                            target_mod = elaborated_file.modules[inst.model]
                            diagnostics.extend(validator.validate_port_mappings(inst_id, inst, target_mod))
            diagnostics.extend(validator.validate_unused_components(elaborated_file))

        exit_code = 1 if has_error(diagnostics) else exit_code

        if json_output:
            payload = {
                "ok": exit_code == 0,
                "stage": "validate",
                "artifacts": {},
                "diagnostics": diagnostics_to_jsonable(diagnostics),
            }
            click.echo(json.dumps(payload, indent=2))
        else:
            print_human_diagnostics(diagnostics, click.echo)

    except click.ClickException as e:
        exit_code = 2
        msg = {"ok": False, "stage": "validate", "diagnostics": [{"code": "CLI", "severity": "ERROR", "title": "CLI error", "message": str(e)}]}
        click.echo(json.dumps(msg, indent=2) if json_output else f"CLI error: {e}")
    except Exception as e:
        exit_code = 3
        msg = {"ok": False, "stage": "validate", "diagnostics": [{"code": "INTERNAL", "severity": "ERROR", "title": "Internal error", "message": str(e)}]}
        click.echo(json.dumps(msg, indent=2) if json_output else f"Unexpected error: {e}")

    sys.exit(exit_code)
