import click

def get_help(self, context):
    """
    If no argument is passed, print help text
    """
    if context.invoked_subcommand is None:
        click.echo(context.get_help())
        return None
