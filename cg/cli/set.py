"""Set data in the status database and LIMS"""
import datetime
import getpass

import click
from cg.apps.lims import LimsAPI
from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS, FLOWCELL_STATUS
from cg.store import Store

CONFIRM = "Continue?"


@click.group("set")
@click.pass_context
def set_cmd(context):
    """Update information in the database."""
    context.obj["status"] = Store(context.obj["database"])
    context.obj["lims"] = LimsAPI(context.obj)


@set_cmd.command()
@click.option("-a", "--action", type=click.Choice(FAMILY_ACTIONS), help="update family action")
@click.option("-p", "--priority", type=click.Choice(PRIORITY_OPTIONS), help="update priority")
@click.option("-g", "--panel", "panels", multiple=True, help="update gene panels")
@click.argument("family_id")
@click.pass_context
def family(context, action, priority, panels, family_id):
    """Update information about a family."""
    family_obj = context.obj["status"].family(family_id)
    if family_obj is None:
        click.echo(click.style(f"Can't find family {family_id}", fg="red"))
        context.abort()
    if not (action or priority or panels):
        click.echo(click.style(f"Nothing to change", fg="yellow"))
        context.abort()
    if action:
        click.echo(
            click.style(f"Update action: {family_obj.action or 'NA'} -> {action}", fg="green")
        )
        family_obj.action = action
    if priority:
        message = f"update priority: {family_obj.priority_human} -> {priority}"
        click.echo(click.style(message, fg="blue"))
        family_obj.priority_human = priority
    if panels:
        for panel_id in panels:
            panel_obj = context.obj["status"].panel(panel_id)
            if panel_obj is None:
                click.echo(click.style(f"unknown gene panel: {panel_id}", fg="red"))
                context.abort()
        message = f"update panels: {', '.join(family_obj.panels)} -> {', '.join(panels)}"
        click.echo(click.style(message, fg="blue"))
        family_obj.panels = panels
    context.obj["status"].commit()


@set_cmd.command()
@click.option(
    "-id",
    "--identifier",
    "identifiers",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    help="Give an identifier on sample and the value to use it with, e.g. -id name Prov52",
)
@click.option(
    "-kv",
    "--key-value",
    "kwargs",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    help="Give a property on sample and the value to set it to, e.g. -kv name Prov52",
)
@click.option("--skip-lims", is_flag=True, help="Skip setting value in LIMS")
@click.option("-y", "--yes", is_flag=True, help="Answer yes on all confirmations")
@click.pass_context
def samples(context, identifiers, kwargs, skip_lims, yes):

    identifier_args = {}
    for identifier_name, identifier_value in identifiers:
        identifier_args[identifier_name] = identifier_value

    samples_objs = context.obj["status"].samples_by_ids(**identifier_args)

    click.echo("Would alter samples:")

    for sample_obj in samples_objs:
        click.echo(f"{sample_obj}")

    if not (yes or click.confirm(CONFIRM)):
        context.abort()

    for sample_obj in samples_objs:
        context.invoke(
            sample, sample_id=sample_obj.internal_id, kwargs=kwargs, yes=yes, skip_lims=skip_lims
        )


@set_cmd.command()
@click.argument("sample_id")
@click.option(
    "-kv",
    "--key-value",
    "kwargs",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    help="Give a property on sample and the value to set it to, e.g. -kv name Prov52",
)
@click.option("--skip-lims", is_flag=True, help="Skip setting value in LIMS")
@click.option("-y", "--yes", is_flag=True, help="Answer yes on all confirmations")
@click.pass_context
def sample(context, sample_id, kwargs, skip_lims, yes):

    sample_obj = context.obj["status"].sample(internal_id=sample_id)

    if sample_obj is None:
        click.echo(click.style(f"Can't find sample {sample_id}", fg="red"))
        context.abort()

    for key, _ in kwargs:

        if key in ["id", "internal_id"]:
            click.echo(click.style(f"{key} not a changeable attribute", fg="red"))
            context.abort()

    for key, value in kwargs:

        new_value = None
        if not hasattr(sample_obj, key):
            click.echo(click.style(f"{key} is not a property of sample", fg="yellow"))
            continue
        if key in ["customer", "application_version"]:
            if key == "customer":
                new_value = context.obj["status"].customer(value)
            elif key == "application_version":
                new_value = context.obj["status"].current_application_version(value)

            if not new_value:
                click.echo(click.style(f"{key} {value} not found, aborting", fg="red"))
                context.abort()
        else:
            new_value = value

        old_value = getattr(sample_obj, key)

        click.echo(f"Would change from {key}={old_value} to {key}={new_value} on {sample_obj}")

        if not (yes or click.confirm(CONFIRM)):
            context.abort()

        setattr(sample_obj, key, new_value)
        _update_comment(_generate_comment(key, old_value, new_value), sample_obj)
        context.obj["status"].commit()

    if not skip_lims:

        for key, value in kwargs:
            click.echo(f"Would set {key} to {value} for {sample_obj.internal_id} in LIMS")

            if not (yes or click.confirm(CONFIRM)):
                context.abort()

            context.obj["lims"].update_sample(lims_id=sample_id, **{key: value})
            click.echo(click.style(f"Set LIMS/{key} to {value}", fg="blue"))


def _generate_comment(what, old_value, new_value):
    return f"\n{what} changed from " f"{str(old_value)} to " f"{str(new_value)}."


def _update_comment(comment, obj):
    """Appends the comment on obj including a timestamp"""
    if comment:
        timestamp = str(datetime.datetime.now())[:-10]
        if obj.comment is None:
            obj.comment = f"{timestamp}-{getpass.getuser()}: {comment}"
        else:
            obj.comment = f"{timestamp}-{getpass.getuser()}: {comment}" + "\n" + obj.comment


@set_cmd.command()
@click.option("-s", "--status", type=click.Choice(FLOWCELL_STATUS))
@click.argument("flowcell_name")
@click.pass_context
def flowcell(context, flowcell_name, status):
    """Update information about a flowcell"""
    flowcell_obj = context.obj["status"].flowcell(flowcell_name)

    if flowcell_obj is None:
        click.echo(click.style(f"flowcell not found: {flowcell_name}", fg="yellow"))
        context.abort()
    prev_status = flowcell_obj.status
    flowcell_obj.status = status

    context.obj["status"].commit()
    click.echo(click.style(f"{flowcell_name} set: {prev_status} -> {status}", fg="green"))

