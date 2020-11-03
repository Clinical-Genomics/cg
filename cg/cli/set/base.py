"""Set data in the status database and LIMS"""
import datetime
import getpass

import click
from cg.apps.lims import LimsAPI
from .families import families
from .family import family
from cg.constants import FAMILY_ACTIONS, PRIORITY_OPTIONS, FLOWCELL_STATUS
from cg.exc import LimsDataError
from cg.store import Store, models

CONFIRM = "Continue?"
HELP_KEY_VALUE = "Give a property on sample and the value to set it to, e.g. -kv name Prov52"
HELP_SKIP_LIMS = "Skip setting value in LIMS"
HELP_YES = "Answer yes on all confirmations"
OPTION_LONG_KEY_VALUE = "--key-value"
OPTION_LONG_SKIP_LIMS = "--skip-lims"
OPTION_LONG_YES = "--yes"
OPTION_SHORT_KEY_VALUE = "-kv"
OPTION_SHORT_YES = "-y"
NOT_CHANGABLE_SAMPLE_ATTRIBUTES = [
    "application_version_id",
    "customer_id",
    "deliveries",
    "flowcells",
    "id",
    "internal_id",
    "invoice",
    "invoice_id",
    "is_external",
    "links",
    "state",
    "to_dict",
]


@click.group("set")
@click.pass_context
def set_cmd(context):
    """Update information in the database."""
    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["lims_api"] = LimsAPI(context.obj)


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
@click.argument("case_id", required=False)
@click.pass_context
def samples(
    context: click.Context,
    identifiers: click.Tuple([str, str]),
    kwargs: click.Tuple([str, str]),
    skip_lims: bool,
    yes: bool,
    case_id: str,
):
    """Set values on many samples at the same time"""
    store = context.obj["status_db"]
    sample_objs = _get_samples(case_id, identifiers, store)

    if not sample_objs:
        click.echo(click.style(fg="red", text="No samples to alter!"))
        context.abort()

    click.echo("Would alter samples:")

    for sample_obj in sample_objs:
        click.echo(f"{sample_obj}")

    if not (yes or click.confirm(CONFIRM)):
        context.abort()

    for sample_obj in sample_objs:
        context.invoke(
            sample, sample_id=sample_obj.internal_id, kwargs=kwargs, yes=yes, skip_lims=skip_lims
        )


def _get_samples(
    case_id: str, identifiers: click.Tuple([str, str]), store: Store
) -> [models.Sample]:
    """Get samples that match both case_id and identifiers if given"""
    samples_by_case_id = None
    samples_by_id = None

    if case_id:
        samples_by_case_id = _get_samples_by_case_id(case_id, store)

    if identifiers:
        samples_by_id = _get_samples_by_identifiers(identifiers, store)

    if case_id and identifiers:
        sample_objs = set(set(samples_by_case_id) & set(samples_by_id))
    else:
        sample_objs = samples_by_case_id or samples_by_id

    return sample_objs


def _get_samples_by_identifiers(
    identifiers: click.Tuple([str, str]), store: Store
) -> models.Sample:
    """Get samples matched by given set of identifiers"""
    identifier_args = {}
    for identifier_name, identifier_value in identifiers:
        identifier_args[identifier_name] = identifier_value
    return store.samples_by_ids(**identifier_args)


def _get_samples_by_case_id(case_id: str, store: Store) -> [models.Sample]:
    """Get samples on a given case-id"""
    case = store.family(internal_id=case_id)
    return [link.sample for link in case.links] if case else []


def is_locked_attribute_on_sample(key, skip_attributes):
    """Returns true if the attribute is private or in the skip list"""
    return is_private_attribute(key) or key in skip_attributes


def is_private_attribute(key):
    """Returns true if key has name indicating it is private"""
    return key.startswith("_")


def list_changeable_sample_attributes(sample_obj: models.Sample = None, skip_attributes: [] = None):
    """List changeable attributes on sample and its current value"""

    sample_attributes = models.Sample.__dict__.keys()
    for attribute in sample_attributes:
        if is_locked_attribute_on_sample(attribute, skip_attributes):
            continue

        message = attribute

        if sample_obj:
            message += f": {sample_obj.__dict__.get(attribute)}"

        click.echo(message)


def show_set_sample_help(sample_obj: models.Sample = "None") -> None:
    """Show help for the set sample command"""
    click.echo("sample_id: optional, internal_id of sample to set value on")
    show_option_help(long_name=OPTION_LONG_SKIP_LIMS, help_text=HELP_SKIP_LIMS)
    show_option_help(short_name=OPTION_SHORT_YES, long_name=OPTION_LONG_YES, help_text=HELP_YES)
    show_option_help(
        short_name=OPTION_SHORT_KEY_VALUE, long_name=OPTION_LONG_KEY_VALUE, help_text=HELP_KEY_VALUE
    )
    list_changeable_sample_attributes(sample_obj, skip_attributes=NOT_CHANGABLE_SAMPLE_ATTRIBUTES)
    click.echo(f"To set apptag use '{OPTION_SHORT_KEY_VALUE} application_version [APPTAG]")
    click.echo(f"To set customer use '{OPTION_SHORT_KEY_VALUE} customer [CUSTOMER]")


def show_option_help(short_name: str = None, long_name: str = None, help_text: str = None):
    """Show help for one option"""
    help_message = f"Use "

    if short_name:
        help_message += f"'{short_name}'"

    if short_name and long_name:
        help_message += " or "

    if long_name:
        help_message += f"'{long_name}'"

    if help_text:
        help_message += f": {help_text}"

    click.echo(help_message)


@set_cmd.command()
@click.argument("sample_id", required=False)
@click.option(
    OPTION_SHORT_KEY_VALUE,
    OPTION_LONG_KEY_VALUE,
    "kwargs",
    nargs=2,
    type=click.Tuple([str, str]),
    multiple=True,
    help=HELP_KEY_VALUE,
)
@click.option(OPTION_LONG_SKIP_LIMS, is_flag=True, help=HELP_SKIP_LIMS)
@click.option(OPTION_SHORT_YES, OPTION_LONG_YES, is_flag=True, help=HELP_YES)
@click.option("--help", is_flag=True)
@click.pass_context
def sample(context, sample_id, kwargs, skip_lims, yes, help):
    sample_obj = context.obj["status_db"].sample(internal_id=sample_id)

    if help:
        show_set_sample_help(sample_obj)

    if sample_obj is None:
        click.echo(click.style(f"Can't find sample {sample_id}", fg="red"))
        context.abort()

    for key, value in kwargs:

        if is_locked_attribute_on_sample(key, NOT_CHANGABLE_SAMPLE_ATTRIBUTES):
            click.echo(click.style(f"{key} is not a changeable attribute on sample", fg="yellow"))
            continue
        if not hasattr(sample_obj, key):
            click.echo(click.style(f"{key} is not a property of sample", fg="yellow"))
            continue
        new_value = None
        if key in ["customer", "application_version"]:
            if key == "customer":
                new_value = context.obj["status_db"].customer(value)
            elif key == "application_version":
                new_value = context.obj["status_db"].current_application_version(value)

            if not new_value:
                click.echo(click.style(f"{key} {value} not found, aborting", fg="red"))
                context.abort()
        else:
            new_value = value

        old_value = getattr(sample_obj, key)

        click.echo(f"Would change from {key}={old_value} to {key}={new_value} on {sample_obj}")

        if not (yes or click.confirm(CONFIRM)):
            continue

        setattr(sample_obj, key, new_value)
        _update_comment(_generate_comment(key, old_value, new_value), sample_obj)
        context.obj["status_db"].commit()

    if not skip_lims:

        for key, value in kwargs:
            click.echo(f"Would set {key} to {value} for {sample_obj.internal_id} in LIMS")

            if not (yes or click.confirm(CONFIRM)):
                context.abort()

            try:
                context.obj["lims_api"].update_sample(lims_id=sample_id, **{key: value})
                click.echo(click.style(f"Set LIMS/{key} to {value}", fg="blue"))
            except LimsDataError as err:
                click.echo(
                    click.style(f"Failed to set LIMS/{key} to {value}, {err.message}", fg="red")
                )


def _generate_comment(what, old_value, new_value):
    """Generate a comment that can be used in the comment field to describe updated value"""
    return f"\n{what} changed from {str(old_value)} to {str(new_value)}."


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
    flowcell_obj = context.obj["status_db"].flowcell(flowcell_name)

    if flowcell_obj is None:
        click.echo(click.style(f"flowcell not found: {flowcell_name}", fg="yellow"))
        context.abort()
    prev_status = flowcell_obj.status
    flowcell_obj.status = status

    context.obj["status_db"].commit()
    click.echo(click.style(f"{flowcell_name} set: {prev_status} -> {status}", fg="green"))


set_cmd.add_command(family)
set_cmd.add_command(families)
