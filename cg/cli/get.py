import logging
import re
from typing import Iterable, List, Optional

import click
from cg.models.cg_config import CGConfig
from cg.store import Store
from tabulate import tabulate

from cg.store.models import Family, Flowcell, Customer, Sample

LOG = logging.getLogger(__name__)
ANALYSIS_HEADERS = ["Analysis Date", "Pipeline", "Version"]
FAMILY_HEADERS = ["Family", "Name", "Customer", "Priority", "Panels", "Action"]
FLOWCELL_HEADERS = ["Flowcell", "Type", "Sequencer", "Date", "Archived?", "Status"]
LINK_HEADERS = ["Sample", "Mother", "Father"]
SAMPLE_HEADERS = ["Sample", "Name", "Customer", "Application", "State", "Priority", "External?"]


@click.group(invoke_without_command=True)
@click.option("-i", "--identifier", help="made a guess what type you are looking for")
@click.pass_context
def get(context: click.Context, identifier: Optional[str]):
    """Get information about records in the database."""
    if identifier:
        if re.match(r"^[A-Z]{3}[0-9]{4,5}[A-Z]{1}[1-9]{1,3}$", identifier):
            context.invoke(sample, sample_ids=[identifier])
        elif re.match(r"^[a-z]*$", identifier):
            # try family information
            context.invoke(family, family_ids=[identifier])
        elif re.match(r"^[HC][A-Z0-9]{8}$", identifier):
            # try flowcell information
            context.invoke(flowcell, flowcell_id=identifier)
        else:
            LOG.error(f"{identifier}: can't predict identifier")
            raise click.Abort


@get.command()
@click.option("--families/--no-families", default=True, help="display related families")
@click.option("-hf", "--hide-flow-cell", is_flag=True, help="hide related flowcells")
@click.argument("sample_ids", nargs=-1)
@click.pass_context
def sample(context: click.Context, families: bool, hide_flow_cell: bool, sample_ids: List[str]):
    """Get information about a sample."""
    status_db: Store = context.obj.status_db
    for sample_id in sample_ids:
        LOG.debug(f"Get info on sample: {sample_id}")
        sample: Sample = status_db.sample(sample_id)
        if sample is None:
            LOG.warning(f"Sample: {sample_id} does not exist")
            continue
        row = [
            sample.internal_id,
            sample.name,
            sample.customer.internal_id,
            sample.application_version.application.tag,
            sample.state,
            sample.priority_human,
            "Yes" if sample.application_version.application.is_external else "No",
        ]
        click.echo(tabulate([row], headers=SAMPLE_HEADERS, tablefmt="psql"))
        if families:
            family_ids: List[str] = [link_obj.family.internal_id for link_obj in sample.links]
            context.invoke(family, family_ids=family_ids, samples=False)
        if not hide_flow_cell:
            for flow_cell in sample.flowcells:
                LOG.debug(f"Get info on flow cell: {flow_cell.name}")
                context.invoke(flowcell, flowcell_id=flow_cell.name, samples=False)


@get.command()
@click.argument("case_id")
@click.pass_obj
def analysis(context: CGConfig, case_id: str):
    """Get information about case analysis."""
    status_db: Store = context.status_db
    case_obj: Family = status_db.family(case_id)
    if case_obj is None:
        LOG.error("%s: case doesn't exist", case_id)
        raise click.Abort

    LOG.debug("%s: get info about case analysis", case_obj.internal_id)

    for analysis_obj in case_obj.analyses:
        row = [
            analysis_obj.started_at,
            analysis_obj.pipeline,
            analysis_obj.pipeline_version,
        ]
        click.echo(tabulate([row], headers=ANALYSIS_HEADERS, tablefmt="psql"))


@get.command()
@click.argument("family_id")
@click.pass_obj
def relations(context: CGConfig, family_id: str):
    """Get information about family relations."""
    status_db: Store = context.status_db
    case_obj: Family = status_db.family(family_id)
    if case_obj is None:
        LOG.error("%s: family doesn't exist", family_id)
        raise click.Abort

    LOG.debug("%s: get info about family relations", case_obj.internal_id)

    for link_obj in case_obj.links:
        row = [
            link_obj.sample.internal_id if link_obj.sample else "",
            link_obj.mother.internal_id if link_obj.mother else "",
            link_obj.father.internal_id if link_obj.father else "",
        ]
        click.echo(tabulate([row], headers=LINK_HEADERS, tablefmt="psql"))


@get.command()
@click.option("-c", "--customer-id", help="internal id for customer to filter by")
@click.option("-n", "--name", is_flag=True, help="search family by name")
@click.option("--samples/--no-samples", default=True, help="display related samples")
@click.option("--relate/--no-relate", default=True, help="display relations to samples")
@click.option("--analyses/--no-analyses", default=True, help="display related analyses")
@click.argument("family_ids", nargs=-1)
@click.pass_context
def family(
    context: click.Context,
    customer_id: str,
    name: bool,
    samples: bool,
    relate: bool,
    analyses: bool,
    family_ids: List[str],
):
    """Get information about a family."""
    status_db: Store = context.obj.status_db
    cases: List[Family] = []
    if name:
        customer_id: Customer = status_db.get_customer_by_customer_id(customer_id=customer_id)
        if customer_id is None:
            LOG.error(f"{customer_id}: customer not found")
            raise click.Abort
        cases: Iterable[Family] = status_db.families(
            customers=[customer_id], enquiry=family_ids[-1]
        )
    else:
        for family_id in family_ids:
            case: Family = status_db.family(family_id)
            if case is None:
                LOG.error(f"{family_id}: family doesn't exist")
                raise click.Abort
            cases.append(case)

    for case in cases:
        LOG.debug(f"{case.internal_id}: get info about family")
        row: List[str] = [
            case.internal_id,
            case.name,
            case.customer.internal_id,
            case.priority_human,
            ", ".join(case.panels),
            case.action or "NA",
        ]
        click.echo(tabulate([row], headers=FAMILY_HEADERS, tablefmt="psql"))
        if relate:
            context.invoke(relations, family_id=case.internal_id)
        if samples:
            sample_ids: List[str] = [link_obj.sample.internal_id for link_obj in case.links]
            context.invoke(sample, sample_ids=sample_ids, families=False)
        if analyses:
            context.invoke(analysis, case_id=case.internal_id)


@get.command()
@click.option("--samples/--no-samples", default=True, help="display related samples")
@click.argument("flowcell_id")
@click.pass_context
def flowcell(context: click.Context, samples: bool, flowcell_id: str):
    """Get information about a flowcell and the samples on it."""
    status_db: Store = context.obj.status_db
    flow_cell: Flowcell = status_db.get_flow_cell(flowcell_id)
    if flow_cell is None:
        LOG.error(f"{flowcell_id}: flow cell not found")
        raise click.Abort
    row: List[str] = [
        flow_cell.name,
        flow_cell.sequencer_type,
        flow_cell.sequencer_name,
        flow_cell.sequenced_at.date(),
        flow_cell.archived_at.date() if flow_cell.archived_at else "No",
        flow_cell.status,
    ]
    click.echo(tabulate([row], headers=FLOWCELL_HEADERS, tablefmt="psql"))
    if samples:
        sample_ids: List[str] = [sample_obj.internal_id for sample_obj in flow_cell.samples]
        if sample_ids:
            context.invoke(sample, sample_ids=sample_ids, families=False)
        else:
            LOG.warning("No samples found on flow cell")
