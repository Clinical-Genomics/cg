import click


@click.command("case")
@click.argument("cases", nargs=-1, required=True, help="List of cases to cancel.")
def case(cases):
    click.echo(f"Running cases: {list(cases)}")
    pass
