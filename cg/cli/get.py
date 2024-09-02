import logging
import re
from typing import Iterable

import click
from tabulate import tabulate

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Customer, IlluminaSequencingRun, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)
ANALYSIS_HEADERS = ["Analysis Date", "Workflow", "Version"]
FAMILY_HEADERS = ["Case", "Name", "Customer", "Priority", "Panels", "Action"]
SEQUENCING_RUN_HEADERS = [
    "Flow Cell",
    "Type",
    "Sequencer",
    "Sequencing started",
    "Sequencing finished",
    "Archived?",
    "Data availability",
]
LINK_HEADERS = ["Sample", "Mother", "Father"]
SAMPLE_HEADERS = ["Sample", "Name", "Customer", "Application", "State", "Priority", "External?"]


@click.group(invoke_without_command=True, context_settings=CLICK_CONTEXT_SETTINGS)
@click.option("-i", "--identifier", help="made a guess what type you are looking for")
@click.pass_context
def get(context: click.Context, identifier: str | None):
    """Get information about records in the database."""
    if identifier:
        if re.match(r"^[A-Z]{3}[0-9]{4,5}[A-Z]{1}[1-9]{1,3}$", identifier):
            context.invoke(get_sample, sample_ids=[identifier])
        elif re.match(r"^[a-z]*$", identifier):
            # try case information
            context.invoke(get_case, case_ids=[identifier])
        elif re.match(r"^[HC][A-Z0-9]{8}$", identifier):
            # try flowcell information
            context.invoke(get_sequencing_run, flow_cell_id=identifier)
        else:
            LOG.error(f"{identifier}: can't predict identifier")
            raise click.Abort


@get.command("sample")
@click.option("--cases/--no-cases", default=True, help="Display related cases")
@click.option("-hf", "--hide-flow-cell", is_flag=True, help="Hide related flow cells")
@click.argument("sample-ids", nargs=-1)
@click.pass_context
def get_sample(context: click.Context, cases: bool, hide_flow_cell: bool, sample_ids: list[str]):
    """Get information about a sample."""
    status_db: Store = context.obj.status_db
    for sample_id in sample_ids:
        LOG.debug(f"{sample_id}: get info about sample")
        existing_sample: Sample = status_db.get_sample_by_internal_id(internal_id=sample_id)
        if existing_sample is None:
            LOG.warning(f"{sample_id}: sample doesn't exist")
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
            case_ids: list[str] = [link_obj.case.internal_id for link_obj in existing_sample.links]
            context.invoke(get_case, case_ids=case_ids, samples=False)
        if not hide_flow_cell:
            for sample_flow_cell in existing_sample.run_devices:
                LOG.debug(f"Get info on flow cell: {sample_flow_cell.internal_id}")
                context.invoke(
                    get_sequencing_run, flow_cell_id=sample_flow_cell.internal_id, samples=False
                )


@get.command("analysis")
@click.argument("case-id")
@click.pass_obj
def get_analysis(context: CGConfig, case_id: str):
    """Get information about case analysis."""
    status_db: Store = context.status_db
    case: Case = status_db.get_case_by_internal_id(internal_id=case_id)
    if case is None:
        LOG.error(f"{case_id}: case doesn't exist")
        raise click.Abort
    LOG.debug(f"{case.internal_id}: get info about case analysis")

    for case_analysis in case.analyses:
        row = [
            case_analysis.started_at,
            case_analysis.workflow,
            case_analysis.workflow_version,
        ]
        click.echo(tabulate([row], headers=ANALYSIS_HEADERS, tablefmt="psql"))


@get.command("relations")
@click.argument("case-id")
@click.pass_obj
def get_case_relations(context: CGConfig, case_id: str):
    """Get information about case relations."""
    status_db: Store = context.status_db
    case: Case = status_db.get_case_by_internal_id(internal_id=case_id)
    if case is None:
        LOG.error(f"{case_id}: case doesn't exist")
        raise click.Abort

    LOG.debug(f"{case.internal_id}: get info about case relations")

    for case_link in case.links:
        row = [
            case_link.sample.internal_id if case_link.sample else "",
            case_link.mother.internal_id if case_link.mother else "",
            case_link.father.internal_id if case_link.father else "",
        ]
        click.echo(tabulate([row], headers=LINK_HEADERS, tablefmt="psql"))


@get.command("case")
@click.option("-c", "--customer-id", help="internal id for customer to filter by")
@click.option("-n", "--name", is_flag=True, help="search family by name")
@click.option("--samples/--no-samples", default=True, help="display related samples")
@click.option("--relate/--no-relate", default=True, help="display relations to samples")
@click.option("--analyses/--no-analyses", default=True, help="display related analyses")
@click.argument("case-ids", nargs=-1)
@click.pass_context
def get_case(
    context: click.Context,
    customer_id: str,
    name: bool,
    samples: bool,
    relate: bool,
    analyses: bool,
    case_ids: list[str],
):
    """Get information about a case."""
    status_db: Store = context.obj.status_db
    status_db_cases: list[Case] = []
    if name:
        customer: Customer = status_db.get_customer_by_internal_id(customer_internal_id=customer_id)
        if not customer:
            LOG.error(f"{customer_id}: customer not found")
            raise click.Abort
        status_db_cases: Iterable[Case] = status_db.get_cases_by_customer_and_case_name_search(
            customer=customer, case_name_search=case_ids[-1]
        )
    else:
        for case_id in case_ids:
            existing_case: Case = status_db.get_case_by_internal_id(internal_id=case_id)
            if not existing_case:
                LOG.error(f"{case_id}: case doesn't exist")
                raise click.Abort
            status_db_cases.append(existing_case)

    for status_db_case in status_db_cases:
        LOG.debug(f"{status_db_case.internal_id}: get info about case")
        row: list[str] = [
            status_db_case.internal_id,
            status_db_case.name,
            status_db_case.customer.internal_id,
            status_db_case.priority_human,
            ", ".join(status_db_case.panels),
            status_db_case.action or "NA",
        ]
        click.echo(tabulate([row], headers=FAMILY_HEADERS, tablefmt="psql"))
        if relate:
            context.invoke(get_case_relations, case_id=status_db_case.internal_id)
        if samples:
            sample_ids: list[str] = [
                link_obj.sample.internal_id for link_obj in status_db_case.links
            ]
            context.invoke(get_sample, sample_ids=sample_ids, cases=False)
        if analyses:
            context.invoke(get_analysis, case_id=status_db_case.internal_id)


@get.command("sequencing-run")
@click.option("--samples/--no-samples", default=True, help="Display related samples")
@click.argument("flow-cell-id")
@click.pass_context
def get_sequencing_run(context: click.Context, samples: bool, flow_cell_id: str):
    """Get information about a sequencing run and its samples, if any."""
    status_db: Store = context.obj.status_db
    sequencing_run: IlluminaSequencingRun = (
        status_db.get_illumina_sequencing_run_by_device_internal_id(device_internal_id=flow_cell_id)
    )
    if not sequencing_run:
        LOG.error(f"Sequencing run with {flow_cell_id} not found")
        raise click.Abort
    row: list[str] = [
        sequencing_run.device.internal_id,
        sequencing_run.sequencer_type,
        sequencing_run.sequencer_name,
        (
            sequencing_run.sequencing_started_at.date()
            if sequencing_run.sequencing_started_at
            else "Not available"
        ),
        sequencing_run.sequencing_completed_at.date(),
        sequencing_run.archived_at.date() if sequencing_run.archived_at else "No",
        sequencing_run.data_availability,
    ]
    click.echo(tabulate([row], headers=SEQUENCING_RUN_HEADERS, tablefmt="psql"))
    if samples:
        sample_ids: list[str] = [
            metric.sample.internal_id for metric in sequencing_run.sample_metrics
        ]
        if sample_ids:
            context.invoke(get_sample, sample_ids=sample_ids, cases=False)
        else:
            LOG.warning("No samples found on sequencing run")
