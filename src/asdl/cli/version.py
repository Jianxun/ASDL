import click
from .. import __version__ as ASDL_VERSION


@click.command("version", help="Print version and environment info")
def version_cmd() -> None:
    click.echo(f"asdlc {ASDL_VERSION}")
