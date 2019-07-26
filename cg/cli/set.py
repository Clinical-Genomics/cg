import logging

import click
import datetime

from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS, FLOWCELL_STATUS
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
    if not (action or priority or panels):
        LOG.error(f"nothing to change")
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
@click.option('-c', '--customer', help='updates customer, input format custXXX.')
@click.option('-C', '--add-comment', 'comment', type=str, help='adds a note/comment to a sample, '
              'put text between quotation marks! This will not overwrite the current comment.')
@click.option('-d', '--downsampled-to', type=int, help='sets number of downsampled \
              total reads. Enter 0 to reset.')
@click.option('-a', '--application-tag', 'apptag', help='sets application tag.')
@click.option('-k', '--capture-kit', help='sets capture kit.')
@click.argument('sample_id')
@click.pass_context
def sample(context, sex, customer, comment, downsampled_to, apptag, capture_kit, sample_id):
    """Update information about a sample."""
    sample_obj = context.obj['status'].sample(sample_id)

    if sample_obj is None:
        print(click.style("can't find sample", fg='red'))
        context.abort()

    if sex:
        print(click.style(f"update sample sex: {sample_obj.sex} -> {sex}", fg='green'))
        sample_obj.sex = sex
        context.obj['status'].commit()

        print(click.style('update LIMS/Gender', fg='blue'))
        if context.obj.get('lims'):
            LimsAPI(context.obj).update_sample(sample_id, sex=sex)

    if customer:
        customer_obj = context.obj['status'].customer(customer)
        if customer_obj is None:
            print(click.style(f"Can't find customer {customer}", fg='red'))
            context.abort()

        previous_customer_obj = context.obj['status'].customer_by_id(sample_obj.customer_id)
        previous_customer = f"{previous_customer_obj.internal_id} ({previous_customer_obj.name})"
        new_customer = f"{customer_obj.internal_id} ({customer_obj.name})"

        if customer_obj.id == sample_obj.customer_id:
            click.echo(click.style(f"Sample {sample_obj.internal_id} already belongs to customer "
                                   f"{previous_customer}", fg='yellow'))
            context.abort()

        click.echo(click.style(f"Update sample customer: {previous_customer} -> {new_customer})",
                               fg='green'))
        sample_obj.customer_id = customer_obj.id
        context.obj['status'].commit()

    if comment:
        timestamp = str(datetime.datetime.now())[:-10]

        if sample_obj.comment is None:
            sample_obj.comment = f"{timestamp}: {comment}"
        else:
            sample_obj.comment += '\n' + f"{timestamp}: {comment}"
        click.echo(click.style(f"Comment added to sample {sample_obj.internal_id}", fg='green'))
        context.obj['status'].commit()

    if downsampled_to or downsampled_to == 0:
        if downsampled_to == 0:
            sample_obj.downsampled_to = None
            message = f"Resetting downsampled total reads for sample {sample_obj.internal_id}."
        else:
            sample_obj.downsampled_to = downsampled_to
            message = f"Number of downsampled total reads set to {downsampled_to} for sample " \
                      f"{sample_obj.internal_id}."
        click.echo(click.style(message, fg='green'))
        context.obj['status'].commit()

    if apptag:
        apptags = [app.tag for app in context.obj['status'].applications()]
        if apptag not in apptags:
            click.echo(click.style(f"Application tag {apptag} does not exist.", fg='red'))
            context.abort()

        application_version = context.obj['status'].current_application_version(apptag)
        if application_version is None:
            click.echo(click.style(f"No valid current application version found!", fg='red'))
            context.abort()

        application_version_id = application_version.id

        if sample_obj.application_version_id == application_version_id:
            click.echo(click.style(f"Sample {sample_obj.internal_id} already has the application "
                                   f"tag {str(application_version)}.", fg='yellow'))
            context.abort()

        sample_obj.application_version_id = application_version_id
        click.echo(click.style(f"Application tag for sample {sample_obj.internal_id} set to "
                               f"{str(application_version)}.", fg='green'))
        context.obj['status'].commit()

    if capture_kit:
        sample_obj.capture_kit = capture_kit
        click.echo(click.style(f"Capture kit {capture_kit} added to sample "
                               f"{sample_obj.internal_id}", fg='green'))
        context.obj['status'].commit()


@set_cmd.command()
@click.option('-s', '--status', type=click.Choice(FLOWCELL_STATUS))
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


@set_cmd.command('microbial-order')
@click.option('-a', '--application-tag', 'apptag', help='sets application tag on all samples in '
                                                        'order.', type=str)
@click.option('-p', '--priority', type=click.Choice(PRIORITY_OPTIONS), help='update priority')
@click.argument('order_id')
@click.argument('user_signature')
@click.pass_context
def microbial_order(context, apptag, priority, order_id, user_signature):
    """Update information on all samples on a microbial order"""

    if not apptag and not priority:
        click.echo(click.style(f"no option specified: {order_id}", fg='yellow'))
        context.abort()

    microbial_order_obj = context.obj['status'].microbial_order(internal_id=order_id)

    if not microbial_order_obj:
        click.echo(click.style(f"order not found: {order_id}", fg='yellow'))
        context.abort()

    for sample_obj in microbial_order_obj.microbial_samples:
        context.invoke(microbial_sample, sample_id=sample_obj.internal_id,
                       user_signature=user_signature, apptag=apptag, priority=priority)


@set_cmd.command('microbial-sample')
@click.option('-a', '--application-tag', 'apptag', help='sets application tag.', type=str)
@click.option('-p', '--priority', type=click.Choice(PRIORITY_OPTIONS), help='update priority')
@click.argument('sample_id')
@click.argument('user_signature')
@click.pass_context
def microbial_sample(context, apptag, priority, sample_id, user_signature):
    """Update information on one sample"""

    sample_obj = context.obj['status'].microbial_sample(internal_id=sample_id)

    if not sample_obj:
        click.echo(click.style(f"sample not found: {sample_id}", fg='yellow'))
        context.abort()

    if not apptag and not priority:
        click.echo(click.style(f"no option specified: {sample_id}", fg='yellow'))
        context.abort()

    if apptag:
        apptags = [app.tag for app in context.obj['status'].applications()]
        if apptag not in apptags:
            click.echo(click.style(f"Application tag {apptag} does not exist.", fg='red'))
            context.abort()

        application_version = context.obj['status'].current_application_version(apptag)
        if application_version is None:
            click.echo(click.style(f"No valid current application version found!", fg='red'))
            context.abort()

        application_version_id = application_version.id

        if sample_obj.application_version_id == application_version_id:
            click.echo(click.style(f"Sample {sample_obj.internal_id} already has the "
                                   f"apptag {str(application_version)}", fg='yellow'))
            return

        comment = f"Application tag changed from" \
            f" {sample_obj.application_version.application} to " \
            f"{str(application_version)} by {user_signature}"
        sample_obj.application_version_id = application_version_id
        click.echo(click.style(f"Application tag for sample {sample_obj.internal_id} set to "
                               f"{str(application_version)}.", fg='green'))

        timestamp = str(datetime.datetime.now())[:-10]
        if sample_obj.comment is None:
            sample_obj.comment = f"{timestamp}: {comment}"
        else:
            sample_obj.comment += '\n' + f"{timestamp}: {comment}"
        click.echo(click.style(f"Comment added to sample {sample_obj.internal_id}", fg='green'))
        context.obj['status'].commit()

        click.echo(click.style('update LIMS/application', fg='blue'))
        if context.obj.get('lims'):
            LimsAPI(context.obj).update_sample(sample_id, application=apptag)

    if priority:
        comment = f"Priority changed from" \
            f" {sample_obj.priority_human} to " \
            f"{str(priority)} by {user_signature}"
        sample_obj.priority_human = priority
        click.echo(click.style(f"priority for sample {sample_obj.internal_id} set to "
                               f"{str(priority)}.", fg='green'))

        timestamp = str(datetime.datetime.now())[:-10]
        if sample_obj.comment is None:
            sample_obj.comment = f"{timestamp}: {comment}"
        else:
            sample_obj.comment += '\n' + f"{timestamp}: {comment}"
        click.echo(click.style(f"Comment added to sample {sample_obj.internal_id}", fg='green'))

        context.obj['status'].commit()

        if context.obj.get('lims'):
            LimsAPI(context.obj).update_sample(sample_id, priority=priority)
