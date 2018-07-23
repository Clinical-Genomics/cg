import logging

import click, datetime

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
@click.option('-c', '--customer', help='update customer, input format custXXX')
@click.option('-n', '--note', 'comment', type=str, help='adds a note/comment to a sample, put text \
              between quotation marks! This will not overwrite the current comment.')
@click.argument('sample_id')
@click.pass_context
def sample(context, sex, customer, comment, sample_id):
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

    if customer:
        customer_obj = context.obj['status'].customer(customer)
        if customer_obj is None:
            print(click.style(f"Can't find customer {customer}", fg='red'))
            context.abort()

        previous_customer_obj = context.obj['status'].customer_by_id(sample_obj.customer_id)
        previous_customer = f"{previous_customer_obj.internal_id} ({previous_customer_obj.name})"
        new_customer = f"{customer_obj.internal_id} ({customer_obj.name})"

        if customer_obj.id == sample_obj.customer_id:
            click.echo(click.style(f"Sample {sample_obj.internal_id} already belongs to customer {previous_customer}", fg='yellow'))
            context.abort()

        click.echo(click.style(f"Update sample customer: {previous_customer} -> {new_customer})", fg='green'))
        sample_obj.customer_id = customer_obj.id
        context.obj['status'].commit()

    if comment:
        timestamp = str(datetime.datetime.now())[:-10]

        if sample_obj.comment == None:
            sample_obj.comment = f"{timestamp}: {comment}"
        else:   
            sample_obj.comment += '\n' + f"{timestamp}: {comment}"
        click.echo(click.style(f"Comment added to sample {sample_obj.internal_id}", fg='green'))
        context.obj['status'].commit()

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
