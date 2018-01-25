import logging

import click

from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS
from cg.store import Store
from cg.apps.lims import LimsAPI

LOG = logging.getLogger(__name__)

@click.group('set')
@click.pass_context
def set_cmd(context):
    """Update information in the database."""
    context.obj['status'] = Store(context.obj['database'])


@set_cmd.command()
@click.option('-a', '--action', type=click.Choice(FAMILY_ACTIONS), help='update family action')
@click.option('-p', '--priority', type=click.Choice(PRIORITY_OPTIONS), help='update priority')
@click.option('-g', '--panel', 'panels', multiple=True, help='update gene panels')
@click.argument('family_id')
@click.pass_context
def family(context, action, priority, panels, family_id):
    """Update information about a family."""
    family_obj = context.obj['status'].family(family_id)
    if family_obj is None:
        LOG.error(f"{family_id}: family not found")
        context.abort()
    if action:
        LOG.info(f"update action: {family_obj.action or 'NA'} -> {action}")
        family_obj.action = action
    if priority:
        message = f"update priority: {family_obj.priority_human} -> {priority}"
        print(click.style(message, fg='blue'))
        family_obj.priority_human = priority
    if panels:
        for panel_id in panels:
            panel_obj = context.obj['status'].panel(panel_id)
            if panel_obj is None:
                print(click.style(f"unknown gene panel: {panel_id}", fg='red'))
                context.abort()
        message = f"update panels: {', '.join(family_obj.panels)} -> {', '.join(panels)}"
        print(click.style(message, fg='blue'))
        family_obj.panels = panels
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

@set_cmd.command()
@click.option('-s', '--status', type=click.Choice(['ondisk', 'removed', 'requested', 'processing']))
@click.argument('flowcell_name')
@click.pass_context
def flowcell(context, flowcell_name, status):
    """Update information about a flowcell"""
    flowcell_obj = context.obj['status'].flowcell(flowcell_name)

    if flowcell_obj is None:
        print(click.style(f"flowcell not found: {flowcell_name}", fg='yellow'))
        context.abort()
    prev_status = flowcell_obj.status
    flowcell_obj.status = status

    context.obj['status'].commit()
    print(click.style(f"{flowcell_name} set: {prev_status} -> {status}", fg='green'))
