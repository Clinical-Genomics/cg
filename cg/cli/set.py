"""Set data in the status database and LIMS"""
import datetime
import getpass
import logging

import click
from cg.apps.lims import LimsAPI
from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS, FLOWCELL_STATUS
from cg.store import Store

LOG = logging.getLogger(__name__)


@click.group("set")
@click.pass_context
def set_cmd(context):
    """Update information in the database."""
    context.obj["status"] = Store(context.obj["database"])
    context.obj["lims"] = LimsAPI(context.obj)


@set_cmd.command()
@click.option(
    "-a", "--action", type=click.Choice(FAMILY_ACTIONS), help="update family action"
)
@click.option(
    "-p", "--priority", type=click.Choice(PRIORITY_OPTIONS), help="update priority"
)
@click.option("-g", "--panel", "panels", multiple=True, help="update gene panels")
@click.argument("family_id")
@click.pass_context
def family(context, action, priority, panels, family_id):
    """Update information about a family."""
    family_obj = context.obj["status"].family(family_id)
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
        print(click.style(message, fg="blue"))
        family_obj.priority_human = priority
    if panels:
        for panel_id in panels:
            panel_obj = context.obj["status"].panel(panel_id)
            if panel_obj is None:
                print(click.style(f"unknown gene panel: {panel_id}", fg="red"))
                context.abort()
        message = (
            f"update panels: {', '.join(family_obj.panels)} -> {', '.join(panels)}"
        )
        print(click.style(message, fg="blue"))
        family_obj.panels = panels
    context.obj["status"].commit()


@set_cmd.command()
@click.option("-s", "--sex", type=click.Choice(["male", "female", "unknown"]))
@click.option("-c", "--customer", help="updates customer, input format custXXX.")
@click.option(
    "-C",
    "--add-comment",
    "comment",
    type=str,
    help="adds a note/comment to a sample, "
    "put text between quotation marks! "
    "This will not overwrite the "
    "current comment.",
)
@click.option(
    "-d",
    "--downsampled-to",
    type=int,
    help="sets number of downsampled \
              total reads. Enter 0 to reset.",
)
@click.option("-a", "--application-tag", "apptag", help="sets application tag.")
@click.option("-k", "--capture-kit", help="sets capture kit.")
@click.option("--data-analysis", help="sets data-analysis.")
@click.option("-n", "--name", help="sets name.")
@click.argument("sample_id")
@click.pass_context
def sample(
    context,
    sex,
    customer,
    comment,
    downsampled_to,
    apptag,
    capture_kit,
    data_analysis,
    name,
    sample_id,
):
    """Update information about a sample."""
    sample_obj = context.obj["status"].sample(sample_id)

    if sample_obj is None:
        click.echo(click.style(f"Can't find sample {sample_id}", fg="red"))
        context.abort()
    else:
        click.echo(click.style(f"Found sample {sample_obj.internal_id}", fg="green"))

    echo_msg = ""

    if comment:
        echo_msg += click.style(f"\nComment added to sample", fg="green")
    else:
        comment = ""

    if name:
        if sample_obj.name != name:
            echo_msg += click.style(
                f"\nUpdate sample name: {sample_obj.name} -> {name}", fg="green"
            )
            comment += _generate_comment("Name", sample_obj.name, name)
            sample_obj.name = name
        else:
            echo_msg += click.style(
                f"\nSample name already: {sample_obj.name}", fg="yellow"
            )

        context.obj["lims"].update_sample(sample_id, name=name)
        click.echo(click.style(f"Set LIMS/Name to {name}", fg="blue"))

    if sex:
        if sample_obj.sex != sex:
            echo_msg += click.style(
                f"\nUpdate sample sex: {sample_obj.sex} -> {sex}", fg="green"
            )
            comment += _generate_comment("Gender", sample_obj.sex, sex)
            sample_obj.sex = sex
        else:
            echo_msg += click.style(
                f"\nSample sex already: {sample_obj.sex}", fg="yellow"
            )

        context.obj["lims"].update_sample(sample_id, sex=sex)
        click.echo(click.style(f"Set LIMS/Gender to {sex}", fg="blue"))

    if customer:
        customer_obj = context.obj["status"].customer(customer)
        if customer_obj is None:
            echo_msg += click.style(f"\nCan't find customer {customer}", fg="red")
        else:
            previous_customer_obj = context.obj["status"].customer_by_id(
                sample_obj.customer_id
            )
            previous_customer = (
                f"{previous_customer_obj.internal_id} "
                f"({previous_customer_obj.name})"
            )
            new_customer = f"{customer_obj.internal_id} ({customer_obj.name})"

            if customer_obj.id == sample_obj.customer_id:
                echo_msg += click.style(
                    f"\nSample already belongs to customer " f"{previous_customer}",
                    fg="yellow",
                )
            else:
                echo_msg += click.style(
                    f"\nUpdate sample customer: {previous_customer} ->"
                    f" {new_customer})",
                    fg="green",
                )
                comment += _generate_comment(
                    "Customer",
                    sample_obj.customer.internal_id,
                    customer_obj.internal_id,
                )
                sample_obj.customer_id = customer_obj.id

    if downsampled_to:
        if downsampled_to != sample_obj.downsampled_to:
            comment += _generate_comment(
                "Total reads", sample_obj.downsampled_to, downsampled_to
            )
            sample_obj.downsampled_to = downsampled_to
            echo_msg += click.style(
                f"\nNumber of downsampled total reads set to {downsampled_to}.",
                fg="green",
            )
        else:
            echo_msg += click.style(
                f"\nSample downsampled already: {sample_obj.downsampled_to}",
                fg="yellow",
            )

    if downsampled_to == 0:
        if sample_obj.downsampled_to:
            comment += _generate_comment("Total reads", sample_obj.downsampled_to, None)
            sample_obj.downsampled_to = None
            echo_msg += click.style(f"\nResetting downsampled total reads.", fg="green")
        else:
            echo_msg += click.style(
                f"\nSample downsampled already: {sample_obj.downsampled_to}",
                fg="yellow",
            )

    if apptag:
        apptags = [app.tag for app in context.obj["status"].applications()]
        if apptag not in apptags:
            echo_msg += click.style(
                f"\nApplication tag {apptag} does not exist.", fg="red"
            )
        else:
            application_version = context.obj["status"].current_application_version(
                apptag
            )
            if application_version is None:
                echo_msg += click.style(
                    f"\nNo valid current application version found!", fg="red"
                )
            else:
                application_version_id = application_version.id

                if sample_obj.application_version_id == application_version_id:
                    echo_msg += click.style(
                        f"\nSample already has the application tag {str(application_version)}.",
                        fg="yellow",
                    )
                else:
                    comment += _generate_comment(
                        "Application tag",
                        sample_obj.application_version_id,
                        application_version_id,
                    )
                    sample_obj.application_version_id = application_version_id
                    echo_msg += click.style(
                        f"\nApplication tag set to {str(application_version)}.",
                        fg="green",
                    )

        context.obj["lims"].update_sample(sample_id, application=apptag)
        click.echo(click.style(f"Set LIMS/application to {apptag}", fg="blue"))

    if capture_kit:
        if sample_obj.capture_kit != capture_kit:
            comment += _generate_comment(
                "Capture kit", sample_obj.capture_kit, capture_kit
            )
            sample_obj.capture_kit = capture_kit
            echo_msg += click.style(f"\nCapture kit {capture_kit} set", fg="green")
        else:
            echo_msg += click.style(
                f"\nSample capture kit already: {sample_obj.capture_kit}", fg="yellow"
            )

    if data_analysis:
        if data_analysis != sample_obj.data_analysis:
            comment += _generate_comment(
                "Data-analysis", sample_obj.data_analysis, data_analysis
            )
            sample_obj.data_analysis = data_analysis
            echo_msg += click.style(f"\nData analysis {data_analysis} set", fg="green")
        else:
            echo_msg += click.style(
                f"\nSample data analysis already: {sample_obj.data_analysis}",
                fg="yellow",
            )

        context.obj["lims"].update_sample(sample_id, data_analysis=data_analysis)
        click.echo(click.style(f"Set LIMS/data_analysis to {data_analysis}", fg="blue"))

    _update_comment(comment, sample_obj)
    context.obj["status"].commit()
    click.echo(echo_msg)


def _generate_comment(what, old_value, new_value):
    return f"\n{what} changed from " f"{str(old_value)} to " f"{str(new_value)}."


def _update_comment(comment, obj):
    """Appends the comment on obj including a timestamp"""
    if comment:
        timestamp = str(datetime.datetime.now())[:-10]
        if obj.comment is None:
            obj.comment = f"{timestamp}-{getpass.getuser()}: {comment}"
        else:
            obj.comment = (
                f"{timestamp}-{getpass.getuser()}: {comment}" + "\n" + obj.comment
            )


@set_cmd.command()
@click.option("-s", "--status", type=click.Choice(FLOWCELL_STATUS))
@click.argument("flowcell_name")
@click.pass_context
def flowcell(context, flowcell_name, status):
    """Update information about a flowcell"""
    flowcell_obj = context.obj["status"].flowcell(flowcell_name)

    if flowcell_obj is None:
        print(click.style(f"flowcell not found: {flowcell_name}", fg="yellow"))
        context.abort()
    prev_status = flowcell_obj.status
    flowcell_obj.status = status

    context.obj["status"].commit()
    print(click.style(f"{flowcell_name} set: {prev_status} -> {status}", fg="green"))


@set_cmd.command("microbial-order")
@click.option(
    "-a",
    "--application-tag",
    "apptag",
    help="sets application tag on all samples in " "order.",
    type=str,
)
@click.option(
    "-p", "--priority", type=click.Choice(PRIORITY_OPTIONS), help="update priority"
)
@click.option("-t", "--ticket", "ticket", help="sets ticket number.", type=str)
@click.option(
    "-n", "--name", "name", help="sets name both in status-db and LIMS.", type=str
)
@click.argument("order_id")
@click.argument("user_signature")
@click.pass_context
def microbial_order(context, apptag, priority, ticket, name, order_id, user_signature):
    """Update information on all samples on a microbial order"""

    if not apptag and not priority and not ticket and not name:
        click.echo(click.style(f"No option specified: {order_id}", fg="yellow"))
        context.abort()

    microbial_order_obj = context.obj["status"].microbial_order(internal_id=order_id)
    if not microbial_order_obj:
        click.echo(click.style(f"order not found: {order_id}", fg="yellow"))
        context.abort()

    if apptag or priority:
        for sample_obj in microbial_order_obj.microbial_samples:
            context.invoke(
                microbial_sample,
                sample_id=sample_obj.internal_id,
                user_signature=user_signature,
                apptag=apptag,
                priority=priority,
            )

    echo_msg = ""

    if ticket:
        if microbial_order_obj.ticket_number == ticket:
            click.echo(
                click.style(
                    f"Order {microbial_order_obj.internal_id} already has the "
                    f"ticket {ticket}",
                    fg="yellow",
                )
            )
            return

        comment = (
            f"Ticket changed from"
            f" {microbial_order_obj.ticket_number} to "
            f"{ticket} by {user_signature}"
        )
        microbial_order_obj.ticket_number = ticket

        echo_msg += click.style(
            f"\nTicket for {microbial_order_obj.internal_id} set to "
            f"{str(microbial_order_obj.ticket_number)}.",
            fg="green",
        )

        _update_comment(comment, microbial_order_obj)
        echo_msg += click.style(
            f"\nComment added to order {microbial_order_obj.internal_id}", fg="green"
        )

    if name:
        if microbial_order_obj.name == name:
            click.echo(
                click.style(
                    f"Order {microbial_order_obj.internal_id} already has the "
                    f"name {name}",
                    fg="yellow",
                )
            )
            return

        comment = (
            f"Name changed from"
            f" {microbial_order_obj.name} to "
            f"{name} by {user_signature}"
        )
        microbial_order_obj.name = name
        echo_msg += click.style(
            f"\nName for {microbial_order_obj.internal_id} set to "
            f"{str(microbial_order_obj.name)}.",
            fg="green",
        )

        _update_comment(comment, microbial_order_obj)
        echo_msg += click.style(
            f"\nComment added to order {microbial_order_obj.internal_id}", fg="green"
        )

        lims_name = f"{name} ({microbial_order_obj.internal_id})"
        context.obj["lims"].update_project(
            microbial_order_obj.internal_id, name=lims_name
        )
        click.echo(click.style(f"updated LIMS/Project-name to {lims_name}", fg="blue"))

    context.obj["status"].commit()
    click.echo(echo_msg)


@set_cmd.command("microbial-sample")
@click.option(
    "-a", "--application-tag", "apptag", help="sets application tag.", type=str
)
@click.option(
    "-p", "--priority", type=click.Choice(PRIORITY_OPTIONS), help="update priority"
)
@click.argument("sample_id")
@click.argument("user_signature")
@click.pass_context
def microbial_sample(context, apptag, priority, sample_id, user_signature):
    """Update information on one sample"""

    sample_obj = context.obj["status"].microbial_sample(internal_id=sample_id)

    if not sample_obj:
        click.echo(click.style(f"Sample not found: {sample_id}", fg="yellow"))
        context.abort()

    if not apptag and not priority:
        click.echo(click.style(f"No option specified: {sample_id}", fg="yellow"))
        context.abort()

    if apptag:
        apptags = [app.tag for app in context.obj["status"].applications()]
        if apptag not in apptags:
            click.echo(
                click.style(f"Application tag {apptag} does not exist.", fg="red")
            )
            context.abort()

        application_version = context.obj["status"].current_application_version(apptag)
        if application_version is None:
            click.echo(
                click.style(f"No valid current application version found!", fg="red")
            )
            context.abort()

        application_version_id = application_version.id

        if sample_obj.application_version_id == application_version_id:
            click.echo(
                click.style(
                    f"Sample {sample_obj.internal_id} already has the "
                    f"apptag {str(application_version)}",
                    fg="yellow",
                )
            )
            return

        comment = (
            f"Application tag changed from"
            f" {sample_obj.application_version.application} to "
            f"{str(application_version)} by {user_signature}"
        )
        sample_obj.application_version_id = application_version_id
        click.echo(
            click.style(
                f"Application tag for sample {sample_obj.internal_id} set to "
                f"{str(application_version)}.",
                fg="green",
            )
        )

        timestamp = str(datetime.datetime.now())[:-10]
        if sample_obj.comment is None:
            sample_obj.comment = f"{timestamp}: {comment}"
        else:
            sample_obj.comment += "\n" + f"{timestamp}: {comment}"
        click.echo(
            click.style(f"Comment added to sample {sample_obj.internal_id}", fg="green")
        )
        context.obj["status"].commit()

        context.obj["lims"].update_sample(sample_id, application=apptag)
        click.echo(click.style("updated LIMS/application", fg="blue"))

    if priority:
        comment = (
            f"Priority changed from"
            f" {sample_obj.priority_human} to "
            f"{str(priority)} by {user_signature}"
        )
        sample_obj.priority_human = priority
        click.echo(
            click.style(
                f"priority for sample {sample_obj.internal_id} set to "
                f"{str(priority)}.",
                fg="green",
            )
        )

        timestamp = str(datetime.datetime.now())[:-10]
        if sample_obj.comment is None:
            sample_obj.comment = f"{timestamp}: {comment}"
        else:
            sample_obj.comment += "\n" + f"{timestamp}: {comment}"
        click.echo(
            click.style(f"Comment added to sample {sample_obj.internal_id}", fg="green")
        )

        context.obj["status"].commit()

        context.obj["lims"].update_sample(sample_id, priority=priority)
        click.echo(click.style("updated LIMS/priority", fg="blue"))
