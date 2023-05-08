"""Set data in the status database and LIMS."""
import datetime
import getpass
import logging
from typing import Iterable, List, Optional

import click
from cg.cli.set.cases import set_cases
from cg.cli.set.case import set_case
from cg.constants import FLOWCELL_STATUS
from cg.exc import LimsDataError
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Sample, Customer, ApplicationVersion, Flowcell

CONFIRM = "Continue?"
HELP_KEY_VALUE = "Give a property on sample and the value to set it to, e.g. -kv name Prov52"
HELP_SKIP_LIMS = "Skip setting value in LIMS"
HELP_YES = "Answer yes on all confirmations"
OPTION_LONG_KEY_VALUE = "--key-value"
OPTION_LONG_SKIP_LIMS = "--skip-lims"
OPTION_LONG_YES = "--yes"
OPTION_SHORT_KEY_VALUE = "-kv"
OPTION_SHORT_YES = "-y"
NOT_CHANGEABLE_SAMPLE_ATTRIBUTES = [
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

LOG = logging.getLogger(__name__)


@click.group("set")
def set_cmd():
    """Update information in the database."""
    pass


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
    """Set values on many samples at the same time."""
    store: Store = context.obj.status_db
    sample_objs: List[Sample] = _get_samples(case_id=case_id, identifiers=identifiers, store=store)

    if not sample_objs:
        LOG.error("No samples to alter!")
        context.abort()

    LOG.info("Would alter samples:")

    for sample_obj in sample_objs:
        LOG.info(f"{sample_obj}")

    if not (yes or click.confirm(CONFIRM)):
        raise click.Abort

    for sample_obj in sample_objs:
        context.invoke(
            sample, sample_id=sample_obj.internal_id, kwargs=kwargs, yes=yes, skip_lims=skip_lims
        )


def _get_samples(case_id: str, identifiers: click.Tuple([str, str]), store: Store) -> List[Sample]:
    """Get samples that match both case_id and identifiers if given."""
    samples_by_case_id = None
    samples_by_id = None

    if case_id:
        samples_by_case_id: List[Sample] = store.get_samples_by_case_id(case_id=case_id)

    if identifiers:
        samples_by_id: List[Sample] = _get_samples_by_identifiers(identifiers, store)

    if case_id and identifiers:
        sample_objs = set(set(samples_by_case_id) & set(samples_by_id))
    else:
        sample_objs = samples_by_case_id or samples_by_id

    return sample_objs


def _get_samples_by_identifiers(identifiers: click.Tuple([str, str]), store: Store) -> List[Sample]:
    """Get samples matched by given set of identifiers."""
    identifier_args = {
        identifier_name: identifier_value for identifier_name, identifier_value in identifiers
    }

    return list(store.get_samples_by_any_id(**identifier_args))


def is_locked_attribute_on_sample(key: str, skip_attributes: List[str]) -> bool:
    """Returns true if the attribute is private or in the skip list."""
    return is_private_attribute(key) or key in skip_attributes


def is_private_attribute(key: str) -> bool:
    """Returns true if key has name indicating it is private."""
    return key.startswith("_")


def list_changeable_sample_attributes(
    sample: Optional[Sample] = None, skip_attributes: List[str] = []
) -> None:
    """List changeable attributes on sample and its current value."""
    LOG.info(f"Below is a set of changeable sample attributes, to combine with -kv flag:\n")

    sample_attributes: Iterable[str] = Sample.__dict__.keys()
    for attribute in sample_attributes:
        if is_locked_attribute_on_sample(attribute, skip_attributes):
            continue
        message: str = attribute
        if sample:
            message += f": {sample.__dict__.get(attribute)}"
        LOG.info(message)


@set_cmd.command()
@click.option("-s", "--sample_id", help="List all available modifiable keys for sample")
@click.pass_obj
def list_keys(
    context: CGConfig,
    sample_id: Optional[str],
):
    """List all available modifiable keys."""
    status_db: Store = context.status_db
    sample: Sample = status_db.get_sample_by_internal_id(internal_id=sample_id)
    list_changeable_sample_attributes(
        sample=sample, skip_attributes=NOT_CHANGEABLE_SAMPLE_ATTRIBUTES
    )


@set_cmd.command()
@click.argument("sample_id", required=True)
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
@click.pass_obj
def sample(
    context: CGConfig,
    sample_id: Optional[str],
    kwargs: click.Tuple([str, str]),
    skip_lims: bool,
    yes: bool,
):
    """Set key values on a sample.

    \b
    To set apptag use: -kv application_version [APPTAG]
    To set customer use: -kv customer [CUSTOMER]
    To set priority use: -kv priority [priority as text or number]

    """
    status_db: Store = context.status_db
    sample: Sample = status_db.get_sample_by_internal_id(internal_id=sample_id)

    if sample is None:
        LOG.error(f"Can't find sample {sample_id}")
        raise click.Abort

    for key, value in kwargs:
        if is_locked_attribute_on_sample(key, NOT_CHANGEABLE_SAMPLE_ATTRIBUTES):
            LOG.warning(f"{key} is not a changeable attribute on sample")
            continue
        if not hasattr(sample, key):
            LOG.warning(f"{key} is not a property of sample")
            continue

        new_key: str = key
        if isinstance(getattr(sample, key), bool):
            new_value: bool = bool(value.lower() == "true")
        else:
            new_value: str = value

        if key in ["customer", "application_version", "priority"]:
            if key == "priority":
                if isinstance(value, str) and not value.isdigit():
                    new_key = "priority_human"
            elif key == "customer":
                new_value: Customer = status_db.get_customer_by_internal_id(
                    customer_internal_id=value
                )
            elif key == "application_version":
                new_value: ApplicationVersion = status_db.get_current_application_version_by_tag(
                    tag=value
                )

            if not new_value:
                LOG.error(f"{key} {value} not found, aborting")
                raise click.Abort

        old_value = getattr(sample, new_key)

        LOG.info(f"Would change from {new_key}={old_value} to {new_key}={new_value} on {sample}")

        if not (yes or click.confirm(CONFIRM)):
            continue

        if key == "comment":
            _update_comment(new_value, sample)
        else:
            setattr(sample, new_key, new_value)
            _update_comment(_generate_comment(new_key, old_value, new_value), sample)

        status_db.session.commit()

    if not skip_lims:
        for key, value in kwargs:
            new_key = "application" if key == "application_version" else key
            new_value = sample.priority_human if key == "priority" else value
            LOG.info(f"Would set {new_key} to {new_value} for {sample.internal_id} in LIMS")

            if not (yes or click.confirm(CONFIRM)):
                raise click.Abort

            try:
                context.lims_api.update_sample(lims_id=sample_id, **{new_key: new_value})
                LOG.info(f"Set LIMS/{new_key} to {new_value}")
            except LimsDataError as error:
                LOG.error(f"Failed to set LIMS/{new_key} to {new_value}, {error}")


def _generate_comment(what, old_value, new_value):
    """Generate a comment that can be used in the comment field to describe updated value."""
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
@click.argument("flow_cell_name")
@click.pass_obj
def flowcell(context: CGConfig, flow_cell_name: str, status: Optional[str]):
    """Update information about a flow cell."""
    status_db: Store = context.status_db
    flowcell_obj: Flowcell = status_db.get_flow_cell_by_name(flow_cell_name=flow_cell_name)

    if flowcell_obj is None:
        LOG.warning(f"flow cell not found: {flow_cell_name}")
        raise click.Abort
    prev_status: str = flowcell_obj.status
    flowcell_obj.status = status

    status_db.session.commit()
    LOG.info(f"{flow_cell_name} set: {prev_status} -> {status}")


set_cmd.add_command(set_case)
set_cmd.add_command(set_cases)
