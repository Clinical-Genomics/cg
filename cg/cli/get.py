import logging
import re
from typing import List

import click
from tabulate import tabulate

from cg.store import Store

LOG = logging.getLogger(__name__)
SAMPLE_HEADERS = ["Sample", "Name", "Customer", "Application", "State", "Priority", "External?"]
FAMILY_HEADERS = ["Family", "Name", "Customer", "Priority", "Panels", "Action"]
LINK_HEADERS = ["Sample", "Mother", "Father"]
FLOWCELL_HEADERS = ["Flowcell", "Type", "Sequencer", "Date", "Archived?", "Status"]


@click.group(invoke_without_command=True)
@click.option("-i", "identifier", help="made a guess what type you are looking for")
@click.pass_context
def get(context: click.Context, identifier: str):
    """Get information about records in the database."""
    context.obj["status_db"] = Store(context.obj["database"])
    if identifier and re.match(r"^[A-Z]{3}[0-9]{4,5}[A-Z]{1}[1-9]{1,3}$", identifier):
        context.invoke(sample, sample_ids=[identifier])
    elif identifier and re.match(r"^[a-z]*$", identifier):
        # try family information
        context.invoke(family, family_ids=[identifier])
    elif identifier and re.match(r"^[HC][A-Z0-9]{8}$", identifier):
        # try flowcell information
        context.invoke(flowcell, flowcell_id=identifier)
    elif identifier:
        LOG.error(f"{identifier}: can't predict identifier")
        context.abort()


@get.command()
@click.option("--families/--no-families", default=True, help="display related families")
@click.option("-f", "--flowcells", is_flag=True, help="display related flowcells")
@click.argument("sample_ids", nargs=-1)
@click.pass_context
def sample(context: click.Context, families: bool, flowcells: bool, sample_ids: List[str]):
    """Get information about a sample."""
    for sample_id in sample_ids:
        LOG.debug("{sample_id}: get info about sample")
        sample_obj = context.obj["status_db"].sample(sample_id)
        if sample_obj is None:
            LOG.warning(f"{sample_id}: sample doesn't exist")
            continue
        row = [
            sample_obj.internal_id,
            sample_obj.name,
            sample_obj.customer.internal_id,
            sample_obj.application_version.application.tag,
            sample_obj.state,
            sample_obj.priority_human,
            "Yes" if sample_obj.application_version.application.is_external else "No",
        ]
        click.echo(tabulate([row], headers=SAMPLE_HEADERS, tablefmt="psql"))
        if families:
            family_ids = [link_obj.family.internal_id for link_obj in sample_obj.links]
            context.invoke(family, family_ids=family_ids, samples=False)
        if flowcells:
            for flowcell_obj in sample_obj.flowcells:
                LOG.debug(f"{flowcell_obj.name}: get info about flowcell")
                context.invoke(flowcell, flowcell_id=flowcell_obj.name, samples=False)


@get.command()
@click.argument("family_id")
@click.pass_context
def relations(context: click.Context, family_id: str):
    """Get information about a family relations."""

    family_obj = context.obj["status_db"].family(family_id)
    if family_obj is None:
        LOG.error("%s: family doesn't exist", family_id)
        context.abort()

    LOG.debug("%s: get info about family relations", family_obj.internal_id)

    for link_obj in family_obj.links:

        row = [
            link_obj.sample.internal_id if link_obj.sample else "",
            link_obj.mother.internal_id if link_obj.mother else "",
            link_obj.father.internal_id if link_obj.father else "",
        ]
        click.echo(tabulate([row], headers=LINK_HEADERS, tablefmt="psql"))


@get.command()
@click.option("-c", "--customer", help="internal id for customer to filter by")
@click.option("-n", "--name", is_flag=True, help="search family by name")
@click.option("--samples/--no-samples", default=True, help="display related samples")
@click.option("--relate/--no-relate", default=True, help="display relations to samples")
@click.argument("family_ids", nargs=-1)
@click.pass_context
def family(
    context: click.Context,
    customer: str,
    name: bool,
    samples: bool,
    relate: bool,
    family_ids: List[str],
):
    """Get information about a family."""
    if name:
        customer_obj = context.obj["status_db"].customer(customer)
        if customer_obj is None:
            LOG.error(f"{customer}: customer not found")
            context.abort()
        families = context.obj["status_db"].families(customer=customer_obj, enquiry=family_ids[-1])
    else:
        families = []
        for family_id in family_ids:
            family_obj = context.obj["status_db"].family(family_id)
            if family_obj is None:
                LOG.error(f"{family_id}: family doesn't exist")
                context.abort()
            families.append(family_obj)

    for family_obj in families:
        LOG.debug(f"{family_obj.internal_id}: get info about family")
        row = [
            family_obj.internal_id,
            family_obj.name,
            family_obj.customer.internal_id,
            family_obj.priority_human,
            ", ".join(family_obj.panels),
            family_obj.action or "NA",
        ]
        click.echo(tabulate([row], headers=FAMILY_HEADERS, tablefmt="psql"))
        if relate:
            context.invoke(relations, family_id=family_obj.internal_id)
        if samples:
            sample_ids = [link_obj.sample.internal_id for link_obj in family_obj.links]
            context.invoke(sample, sample_ids=sample_ids, families=False)


@get.command()
@click.option("--samples/--no-samples", default=True, help="display related samples")
@click.argument("flowcell_id")
@click.pass_context
def flowcell(context: click.Context, samples: bool, flowcell_id: str):
    """Get information about a flowcell and the samples on it."""
    flowcell_obj = context.obj["status_db"].flowcell(flowcell_id)
    if flowcell_obj is None:
        LOG.error(f"{flowcell_id}: flowcell not found")
        context.abort()
    row = [
        flowcell_obj.name,
        flowcell_obj.sequencer_type,
        flowcell_obj.sequencer_name,
        flowcell_obj.sequenced_at.date(),
        flowcell_obj.archived_at.date() if flowcell_obj.archived_at else "No",
        flowcell_obj.status,
    ]
    click.echo(tabulate([row], headers=FLOWCELL_HEADERS, tablefmt="psql"))
    if samples:
        sample_ids = [sample_obj.internal_id for sample_obj in flowcell_obj.samples]
        if sample_ids:
            context.invoke(sample, sample_ids=sample_ids, families=False)
        else:
            LOG.warning("no samples found on flowcell")
