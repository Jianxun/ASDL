import json
from pathlib import Path
from typing import Optional

import click

from ..data_structures import build_json_schema, render_text_schema


@click.command("schema", help="Print ASDL schema (text by default, or JSON with --json)")
@click.option("--json", "json_output", is_flag=True, help="Emit JSON Schema to stdout")
@click.option(
    "--out",
    type=click.Path(dir_okay=True, file_okay=False, path_type=Path),
    default=None,
    help="Optional directory path to also write schema.json and schema.txt",
)
def schema_cmd(json_output: bool, out: Optional[Path]) -> None:
    if json_output:
        schema = build_json_schema()
        click.echo(json.dumps(schema, indent=2, ensure_ascii=False))
    else:
        click.echo(render_text_schema())

    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
        (out / "schema.json").write_text(
            json.dumps(build_json_schema(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (out / "schema.txt").write_text(render_text_schema(), encoding="utf-8")


