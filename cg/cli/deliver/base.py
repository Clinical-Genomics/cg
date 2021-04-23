"""CLI for delivering files with CG"""
import logging
from pathlib import Path
from typing import List, Optional

import click
from cg.constants.delivery import PIPELINE_ANALYSIS_OPTIONS, PIPELINE_ANALYSIS_TAG_MAP
from cg.meta.deliver import DeliverAPI
from cg.meta.rsync import RsyncAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.group()
def deliver():
    """Deliver files with CG."""
    LOG.info("Running CG deliver")


@deliver.command(name="analysis")
@click.option("-c", "--case-id", help="Deliver the files for a specific case")
@click.option(
    "-t", "--ticket-id", type=int, help="Deliver the files for ALL cases connected to a ticket"
)
@click.option("-d", "--delivery-type", type=click.Choice(PIPELINE_ANALYSIS_OPTIONS), required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def deliver_analysis(
    context: CGConfig,
    case_id: Optional[str],
    ticket_id: Optional[int],
    delivery_type: str,
    dry_run: bool,
):
    """Deliver analysis files to customer inbox

    Files can be delivered either on case level or for all cases connected to a ticket.
    Any of those needs to be specified.
    """
    if not (case_id or ticket_id):
        LOG.info("Please provide a case-id or ticket-id")
        return

    inbox: str = context.delivery_path
    if not inbox:
        LOG.info("Please specify the root path for where files should be delivered")
        return

    status_db: Store = context.status_db
    deliver_api = DeliverAPI(
        store=status_db,
        hk_api=context.housekeeper_api,
        case_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["case_tags"],
        sample_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery_type]["sample_tags"],
        project_base_path=Path(inbox),
        delivery_type=delivery_type,
    )
    deliver_api.set_dry_run(dry_run)
    cases: List[models.Family] = []
    if case_id:
        case_obj: models.Family = status_db.family(case_id)
        if not case_obj:
            LOG.warning("Could not find case %s", case_id)
            return
        cases.append(case_obj)
    else:
        cases = status_db.get_cases_from_ticket(ticket_id=ticket_id).all()
        if not cases:
            LOG.warning("Could not find cases for ticket_id %s", ticket_id)
            return

    for case_obj in cases:
        deliver_api.deliver_files(case_obj=case_obj)


@deliver.command(name="rsync")
@click.argument("ticket_id", type=int, required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def rsync(context: CGConfig, ticket_id: int, dry_run: bool):
    """The folder generated using the "cg deliver analysis" command will be
    rsynced with this function to the customers inbox on caesar.
    """
    rsync_api = RsyncAPI(config=context)
    rsync_api.run_rsync_command(ticket_id=ticket_id, dry_run=dry_run)
