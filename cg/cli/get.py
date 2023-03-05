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
            context.invoke(family, case_ids=[identifier])
        elif re.match(r"^[HC][A-Z0-9]{8}$", identifier):
            # try flowcell information
            context.invoke(flowcell, flow_cell_id=identifier)
        else:
            LOG.error(f"{identifier}: can't predict identifier")
            raise click.Abort


@get.command()
@click.option("--cases/--no-cases", default=True, help="Display related cases")
@click.option("-hf", "--hide-flow-cell", is_flag=True, help="Hide related flow cells")
@click.argument("sample-ids", nargs=-1)
@click.pass_context
def sample(context: click.Context, cases: bool, hide_flow_cell: bool, sample_ids: List[str]):
    """Get information about a sample."""
    status_db: Store = context.obj.status_db
    for sample_id in sample_ids:
        LOG.debug(f"Get info on sample: {sample_id}")
        existing_sample: Sample = status_db.sample(sample_id)
        if existing_sample is None:
            LOG.warning(f"Sample: {sample_id} does not exist")
            continue
        row = [
            existing_sample.internal_id,
            existing_sample.name,
            existing_sample.customer.internal_id,
            existing_sample.application_version.application.tag,
            existing_sample.state,
            existing_sample.priority_human,
            "Yes" if existing_sample.application_version.application.is_external else "No",
        ]
        click.echo(tabulate([row], headers=SAMPLE_HEADERS, tablefmt="psql"))
        if cases:
            case_ids: List[str] = [
                link_obj.family.internal_id for link_obj in existing_sample.links
            ]
            context.invoke(family, case_ids=case_ids, samples=False)
        if not hide_flow_cell:
            for flow_cell in existing_sample.flowcells:
                LOG.debug(f"Get info on flow cell: {flow_cell.name}")
                context.invoke(flowcell, flow_cell_id=flow_cell.name, samples=False)


@get.command()
@click.argument("case-id")
@click.pass_obj
def analysis(context: CGConfig, case_id: str):
    """Get information about case analysis."""
    status_db: Store = context.status_db
    case: Family = status_db.family(case_id)
    if case is None:
        LOG.error(f"{case_id}: case doesn't exist")
        raise click.Abort
    LOG.debug(f"{case.internal_id}: get info about case analysis")

    for case_analysis in case.analyses:
        row = [
            case_analysis.started_at,
            case_analysis.pipeline,
            case_analysis.pipeline_version,
        ]
        click.echo(tabulate([row], headers=ANALYSIS_HEADERS, tablefmt="psql"))


@get.command()
@click.argument("case-id")
@click.pass_obj
def relations(context: CGConfig, case_id: str):
    """Get information about case relations."""
    status_db: Store = context.status_db
    case: Family = status_db.family(internal_id=case_id)
    if case is None:
        LOG.error(f"{case_id}: family doesn't exist")
        raise click.Abort

    LOG.debug(f"{case.internal_id}: get info about family relations")

    for case_link in case.links:
        row = [
            case_link.sample.internal_id if case_link.sample else "",
            case_link.mother.internal_id if case_link.mother else "",
            case_link.father.internal_id if case_link.father else "",
        ]
        click.echo(tabulate([row], headers=LINK_HEADERS, tablefmt="psql"))


@get.command()
@click.option("-c", "--customer-id", help="internal id for customer to filter by")
@click.option("-n", "--name", is_flag=True, help="search family by name")
@click.option("--samples/--no-samples", default=True, help="display related samples")
@click.option("--relate/--no-relate", default=True, help="display relations to samples")
@click.option("--analyses/--no-analyses", default=True, help="display related analyses")
@click.argument("case-ids", nargs=-1)
@click.pass_context
def family(
    context: click.Context,
    customer_id: str,
    name: bool,
    samples: bool,
    relate: bool,
    analyses: bool,
    case_ids: List[str],
):
    """Get information about a case."""
    status_db: Store = context.obj.status_db
    cases: List[Family] = []
    if name:
        customer_id: Customer = status_db.get_customer_by_customer_id(customer_id=customer_id)
        if customer_id is None:
            LOG.error(f"{customer_id}: customer not found")
            raise click.Abort
        cases: Iterable[Family] = status_db.families(customers=[customer_id], enquiry=case_ids[-1])
    else:
        for family_id in case_ids:
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
            context.invoke(relations, case_id=case.internal_id)
        if samples:
            sample_ids: List[str] = [link_obj.sample.internal_id for link_obj in case.links]
            context.invoke(sample, sample_ids=sample_ids, cases=False)
        if analyses:
            context.invoke(analysis, case_id=case.internal_id)


@get.command()
@click.option("--samples/--no-samples", default=True, help="display related samples")
@click.argument("flow-cell-id")
@click.pass_context
def flowcell(context: click.Context, samples: bool, flow_cell_id: str):
    """Get information about a flowcell and the samples on it."""
    status_db: Store = context.obj.status_db
    flow_cell: Flowcell = status_db.get_flow_cell(flow_cell_id)
    if flow_cell is None:
        LOG.error(f"{flow_cell_id}: flow cell not found")
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
            context.invoke(sample, sample_ids=sample_ids, cases=False)
        else:
            LOG.warning("No samples found on flow cell")
