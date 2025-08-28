import json
import sys
from pathlib import Path
from typing import Optional, List

import click

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
@click.option("-v", "--verbose", is_flag=True, help="Verbose logs")
@click.option("--top", type=str, help="Override top module")
@click.option("--search-path", "search_paths", multiple=True, type=click.Path(path_type=Path), help="Additional search paths for import resolution (can be repeated)")
@click.option("--top-style", type=click.Choice([e.value for e in TopStyle], case_sensitive=False), default=TopStyle.SUBCKT.value, help="Top-level emission style: subckt (default) or flat (comment wrappers)")
def netlist_cmd(input: Path, output: Optional[Path], json_output: bool, verbose: bool, top: Optional[str], search_paths: Optional[List[Path]], top_style: str) -> None:
    exit_code = 0
    diagnostics: List[Diagnostic] = []
    artifact_path: Optional[Path] = None

    try:
        elaborator = Elaborator()
        if verbose:
            click.echo("[imports] resolving…")
        elaborated_file, elab_diags = elaborator.elaborate_with_imports(
            input, search_paths=list(search_paths) if search_paths else None, top=top
        )
        diagnostics.extend(elab_diags)

        if elaborated_file is None:
            exit_code = 1
        else:
            if verbose:
                click.echo("[validate] running structural checks…")
            validator = ASDLValidator()
            diagnostics.extend(validator.validate_file(elaborated_file))
            
            # If there are any prior ERROR diagnostics, skip generation
            if not has_error(diagnostics):
                if verbose:
                    click.echo("[generate] writing SPICE netlist…")
                gen_options = GeneratorOptions(top_style=TopStyle(top_style))
                generator = SPICEGenerator(options=gen_options)
                netlist_str, generator_diags = generator.generate(elaborated_file)
                diagnostics.extend(generator_diags)
                artifact_path = output if output else input.with_suffix(".spice")
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
            if verbose and artifact_path:
                click.echo(f"netlist written to: {artifact_path}")

    except click.ClickException as e:
        exit_code = 2
        msg = {"ok": False, "stage": "netlist", "diagnostics": [{"code": "CLI", "severity": "ERROR", "title": "CLI error", "message": str(e)}]}
        click.echo(json.dumps(msg, indent=2) if json_output else f"CLI error: {e}")

    sys.exit(exit_code)
