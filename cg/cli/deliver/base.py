"""CLI for delivering files with CG"""

import logging

from typing import List
from pathlib import Path

import click

from cg.meta.deliver import DeliverAPI
from cg.store import Store
from cg.store.models import Family
from cg.apps.hk import HousekeeperAPI
from cg.constants.delivery import (
    PIPELINE_ANALYSIS_OPTIONS,
    PIPELINE_ANALYSIS_TAG_MAP,
)

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
def deliver(context):
    """Deliver files with CG."""
    LOG.info("Running CG deliver")
    context.obj["status_db"] = Store(context.obj["database"])
    context.obj["housekeeper_api"] = HousekeeperAPI(context.obj)


@click.command(name="analysis")
@click.option("-c", "--case-id")
@click.option("-t", "--ticket-id", type=int)
@click.option("-d", "--delivery-type", type=click.Choice(PIPELINE_ANALYSIS_OPTIONS), required=True)
@click.option(
    "-i",
    "--inbox",
    help="customer inbox",
)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def deliver_analysis(
    context, case_id: str, ticket_id: int, delivery_type: str, inbox: str, dry_run: bool
):
    """Deliver analysis files to customer inbox"""
    if not (case_id or ticket_id):
        LOG.info("Please provide a case-id or ticket-id")
        return
    inbox = inbox or context.obj.get("delivery_path")
    if not inbox:
        LOG.info("Please specify the root path for where files should be delivered")
        return

    status_db: Store = context.obj["status_db"]
    deliver_api = DeliverAPI(
        store=status_db,
        hk_api=context.obj["housekeeper_api"],
        case_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["case_tags"],
        sample_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["sample_tags"],
        project_base_path=Path(inbox),
    )
    deliver_api.set_dry_run(dry_run)
    if case_id:
        case_obj = status_db.family(case_id)
        if not case_obj:
            LOG.warning("Could not find case %s", case_id)
            return
        cases = [case_obj]
    else:
        cases: List[Family] = status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        if not cases:
            LOG.warning("Could not find cases for ticket_id %s", ticket_id)
            return

    for case_obj in cases:
        deliver_api.deliver_files(case_obj=case_obj)


deliver.add_command(deliver_analysis)
