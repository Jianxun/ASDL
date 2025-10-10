import json
import sys
from pathlib import Path
from typing import Optional, List

import click
from ..logging_utils import get_logger, configure_logging

from ..parser import ASDLParser
from ..elaborator import Elaborator
from ..generator import SPICEGenerator
from ..generator.options import GeneratorOptions, TopStyle
from ..validator import ASDLValidator
from ..diagnostics import Diagnostic
from .helpers import diagnostics_to_jsonable, has_error, print_human_diagnostics


@click.command("netlist", help="Parse → elaborate → validate → generate SPICE netlist")
@click.argument("input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path), help="Output SPICE file (default: input with .spice)")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON to stdout")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logs (INFO level)")
@click.option("--top", type=str, help="Override top module")
@click.option("--top-style", type=click.Choice([e.value for e in TopStyle], case_sensitive=False), default=TopStyle.FLAT.value, help="Top-level emission style: subckt (default) or flat (comment wrappers)")
@click.option("-t", "--template", is_flag=True, help="Emit Jinja2 template: skip unresolved placeholder checks and default output to .spice.j2")
@click.pass_context
def netlist_cmd(ctx: click.Context, input: Path, output: Optional[Path], json_output: bool, verbose: bool, top: Optional[str], top_style: str, template: bool) -> None:
    exit_code = 0
    diagnostics: List[Diagnostic] = []
    artifact_path: Optional[Path] = None

    try:
        configure_logging(
            verbose=verbose,
            debug=ctx.obj.get("debug", False),
            trace=ctx.obj.get("trace", False),
            log_file=ctx.obj.get("log_file"),
            log_json=ctx.obj.get("log_json"),
        )
        log = get_logger("cli")
        elaborator = Elaborator()
        log.info("[imports] resolving…")
        elaborated_file, elab_diags = elaborator.elaborate_with_imports(input, top=top)
        diagnostics.extend(elab_diags)

        if elaborated_file is None:
            exit_code = 1
        else:
            log.info("[validate] running structural checks…")
            validator = ASDLValidator()
            diagnostics.extend(validator.validate_file(elaborated_file))
            
            # If there are any prior ERROR diagnostics, skip generation
            if not has_error(diagnostics):
                log.info("[generate] writing SPICE netlist…")
                gen_options = GeneratorOptions(top_style=TopStyle(top_style), template_mode=template)
                generator = SPICEGenerator(options=gen_options)
                netlist_str, generator_diags = generator.generate(elaborated_file)
                diagnostics.extend(generator_diags)
                if output:
                    artifact_path = output
                else:
                    # Default naming: *.spice (normal) or *.spice.j2 (template mode)
                    if template:
                        artifact_path = input.with_suffix(".spice.j2")
                    else:
                        artifact_path = input.with_suffix(".spice")
                artifact_path.parent.mkdir(parents=True, exist_ok=True)
                artifact_path.write_text(netlist_str, encoding="utf-8")

        exit_code = 1 if has_error(diagnostics) else exit_code

        if json_output:
            payload = {
                "ok": exit_code == 0,
                "stage": "netlist",
                "artifacts": {"netlist": str(artifact_path) if artifact_path else None},
                "diagnostics": diagnostics_to_jsonable(diagnostics),
            }
            click.echo(json.dumps(payload, indent=2))
        else:
            print_human_diagnostics(diagnostics, click.echo)
            if artifact_path:
                log.info(f"netlist written to: {artifact_path}")

    except click.ClickException as e:
        exit_code = 2
        msg = {"ok": False, "stage": "netlist", "diagnostics": [{"code": "CLI", "severity": "ERROR", "title": "CLI error", "message": str(e)}]}
        click.echo(json.dumps(msg, indent=2) if json_output else f"CLI error: {e}")

    sys.exit(exit_code)
