import click


@click.command("diag-codes", help="List known diagnostic code prefixes (XCCSS)")
def diag_codes_cmd() -> None:
    click.echo("XCCSS diagnostic code prefixes: P (Parser), E (Elaborator), V (Validator), G (Generator), I (Importer), S (Schema)")
