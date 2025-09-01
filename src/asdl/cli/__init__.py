import click
from ..logging_utils import configure_logging

from .. import __version__ as ASDL_VERSION
from .version import version_cmd
from .diag_codes import diag_codes_cmd
from .validate import validate_cmd
from .elaborate import elaborate_cmd
from .netlist import netlist_cmd
from .schema import schema_cmd


@click.group(help="ASDL compiler CLI: parse → elaborate → validate → netlist")
@click.version_option(ASDL_VERSION, prog_name="asdlc")
@click.option("--debug", is_flag=True, help="Enable DEBUG logs")
@click.option("--trace", is_flag=True, help="Enable TRACE logs (very verbose)")
@click.option("--log-file", type=click.Path(dir_okay=False), help="Write logs to specified file")
@click.option("--log-json", is_flag=True, help="Emit logs in JSON format")
@click.pass_context
def cli(ctx: click.Context, debug: bool, trace: bool, log_file: str | None, log_json: bool) -> None:
    # Configure base logging (no verbose by default); commands may reconfigure with -v
    configure_logging(debug=debug, trace=trace, log_file=log_file, log_json=log_json)
    ctx.ensure_object(dict)
    ctx.obj.update({
        "debug": debug,
        "trace": trace,
        "log_file": log_file,
        "log_json": log_json,
    })

# Register commands
cli.add_command(version_cmd)
cli.add_command(diag_codes_cmd)
cli.add_command(validate_cmd)
cli.add_command(elaborate_cmd)
cli.add_command(netlist_cmd)
cli.add_command(schema_cmd)
