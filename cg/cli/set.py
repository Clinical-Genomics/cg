import click

from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS
from cg.store import Store


@click.group('set')
@click.pass_context
def set_cmd(context):
    """Update information in the database."""
    context.obj['status'] = Store(context.obj['database'])


@set_cmd.command()
@click.option('-a', '--action', type=click.Choice(FAMILY_ACTIONS), help='update family action')
@click.option('-p', '--priority', type=click.Choice(PRIORITY_OPTIONS), help='update priority')
@click.argument('family_id')
@click.pass_context
def family(context, action, priority, family_id):
    """Update information about a family."""
    family_obj = context.obj['status'].family(family_id)
    if family_obj is None:
        click.echo(click.style("can't find family", fg='red'))
        context.abort()
    if action:
        message = f"updating action: {family_obj.action or 'NA'} -> {action}"
        click.echo(click.style(message, fg='blue'))
        family_obj.action = action
    if priority:
        message = f"updating priority: {family_obj.priority_human} -> {priority}"
        click.echo(click.style(message, fg='blue'))
        family_obj.priority_human = priority
    context.obj['status'].commit()
