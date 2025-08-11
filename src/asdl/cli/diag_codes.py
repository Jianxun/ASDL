import click


@click.command("diag-codes", help="List known diagnostic codes (stub)")
def diag_codes_cmd() -> None:
    click.echo("Known diagnostic code prefixes: P*** (parser), E*** (elaborator), V*** (validator)")
