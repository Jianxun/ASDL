import click

from .. import __version__ as ASDL_VERSION
from .version import version_cmd
from .diag_codes import diag_codes_cmd
from .validate import validate_cmd
from .elaborate import elaborate_cmd
from .netlist import netlist_cmd
from .schema import schema_cmd


@click.group(help="ASDL compiler CLI: parse → elaborate → validate → netlist")
@click.version_option(ASDL_VERSION, prog_name="asdlc")
def cli() -> None:
    pass

# Register commands
cli.add_command(version_cmd)
cli.add_command(diag_codes_cmd)
cli.add_command(validate_cmd)
cli.add_command(elaborate_cmd)
cli.add_command(netlist_cmd)
cli.add_command(schema_cmd)
