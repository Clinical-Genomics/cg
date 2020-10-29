"""CLI for delivering files with CG"""

import logging

import click

from cg.meta.deliver import DeliverAPI
from cg.store import Store
from cg.store.models import Family
from cg.apps.hk import HousekeeperAPI
from cg.constants.delivery import (
    PIPELINE_ANALYSIS_OPTIONS,
    PROJECT_BASE_PATH,
    PIPELINE_ANALYSIS_TAG_MAP,
)

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def deliver(context):
    """Deliver files with CG."""
    LOG.info("Running CG DEPLOY")
    context.obj["store"] = Store(context.obj["database"])
    context.obj["hk_api"] = HousekeeperAPI(context.obj)


@click.command(name="analysis")
@click.option("-c", "--case-id")
@click.option("-t", "--ticket-id", type=int)
@click.option("-t", "--analysis-type", type=click.Option(PIPELINE_ANALYSIS_OPTIONS))
@click.option(
    "-i",
    "--inbox",
    default=PROJECT_BASE_PATH,
    show_default=True,
    help="customer inbox",
)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def deliver_analysis(context, case_id, ticket_id, analysis_type, inbox, dry_run):
    """Deliver analysis files to customer inbox"""
    if not case_id or ticket_id:
        LOG.info("Please provide a case-id or ticket-id")
        return
    store: Store = context.obj["store"]
    deliver_api = DeliverAPI(
        store=store,
        hk_api=context.obj["hk_api"],
        case_tags=PIPELINE_ANALYSIS_TAG_MAP[analysis_type]["case_tags"],
        sample_tags=PIPELINE_ANALYSIS_TAG_MAP[analysis_type]["sample_tags"],
        project_base_path=inbox,
    )
    deliver_api.set_dry_run(dry_run)
    if case_id:
        case_obj = store.family(case_id)
        if not case_obj:
            LOG.warning("Could not find case %s", case_id)
            return
        cases = [case_obj]
    else:
        cases: List[Family] = [case for case in store.get_cases_from_ticket(ticket_id=ticket_id)]
        if not cases:
            LOG.warning("Could not find cases for ticket_id %s", ticket_id)
            return

    for case_obj in cases:
        deliver_api.deliver_files(case_obj=case_obj)
