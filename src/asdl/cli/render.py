import json
from pathlib import Path
from typing import Optional, Any, Dict

import click
import yaml
from jinja2 import Environment, StrictUndefined

from ..logging_utils import get_logger, configure_logging


def _load_context(ctx_path: Path) -> Dict[str, Any]:
    text = ctx_path.read_text(encoding="utf-8")
    lower = ctx_path.suffix.lower()
    if lower in (".yml", ".yaml"):
        return yaml.safe_load(text) or {}
    if lower == ".json":
        return json.loads(text)
    # Fallback: try YAML first, then JSON
    try:
        return yaml.safe_load(text) or {}
    except Exception:
        return json.loads(text)


@click.command("render", help="Render a Jinja2 SPICE template (.j2) with a context file")
@click.argument("template", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-c", "--context", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True, help="YAML/JSON context file")
@click.option("-o", "--output", type=click.Path(dir_okay=False, path_type=Path), help="Output SPICE filename (default: template filename without trailing .j2)")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logs (INFO level)")
@click.pass_context
def render_cmd(ctx: click.Context, template: Path, context: Path, output: Optional[Path], verbose: bool) -> None:
    configure_logging(
        verbose=verbose,
        debug=ctx.obj.get("debug", False),
        trace=ctx.obj.get("trace", False),
        log_file=ctx.obj.get("log_file"),
        log_json=ctx.obj.get("log_json"),
    )
    log = get_logger("cli")

    env = Environment(undefined=StrictUndefined, autoescape=False)
    tmpl = env.from_string(template.read_text(encoding="utf-8"))
    data = _load_context(context)
    rendered = tmpl.render(**data)

    if output is None:
        # Strip exactly one trailing .j2
        if template.name.endswith(".j2"):
            out = template.with_name(template.name[:-3])
        else:
            out = template.with_suffix("")
        output = out

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    log.info(f"rendered output written to: {output}")


