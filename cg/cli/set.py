import click

from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS
from cg.store import Store
from cg.apps.lims import LimsAPI


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
        print(click.style("can't find family", fg='red'))
        context.abort()
    if action:
        message = f"updating action: {family_obj.action or 'NA'} -> {action}"
        print(click.style(message, fg='blue'))
        family_obj.action = action
    if priority:
        message = f"updating priority: {family_obj.priority_human} -> {priority}"
        print(click.style(message, fg='blue'))
        family_obj.priority_human = priority
    context.obj['status'].commit()


@set_cmd.command()
@click.option('-s', '--sex', type=click.Choice(['male', 'female', 'unknown']))
@click.argument('sample_id')
@click.pass_context
def sample(context, sex, sample_id):
    """Update information about a sample."""
    lims_api = LimsAPI(context.obj)
    sample_obj = context.obj['status'].sample(sample_id)

    if sample_obj is None:
        print(click.style("can't find sample", fg='red'))
        context.abort()

    if sex:
        print(click.style(f"update sample sex: {sample_obj.sex} -> {sex}", fg='green'))
        sample_obj.sex = sex
        context.obj['status'].commit()

        print(click.style('update LIMS/Gender', fg='blue'))
        lims_api.update_sample(sample_id, sex=sex)
