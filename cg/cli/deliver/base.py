"""CLI for delivering files with CG"""
import logging
from pathlib import Path
from typing import List, Optional

import click
from cg.constants.delivery import PIPELINE_ANALYSIS_OPTIONS, PIPELINE_ANALYSIS_TAG_MAP
from cg.meta.deliver import DeliverAPI
from cg.meta.deliver_ticket import DeliverTicketAPI
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


@deliver.command(name="concatenate")
@click.argument("ticket_id", type=int, required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def concatenate(context: click.Context, ticket_id: int, dry_run: bool):
    """The fastq files in the folder generated using "cg deliver analysis"
    will be concatenated into one forward and one reverse fastq file.
    """
    cg_context: CGConfig = context.obj
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)
    deliver_ticket_api.concatenate(ticket_id=ticket_id, dry_run=dry_run)


@deliver.command(name="ticket")
@click.option(
    "-t",
    "--ticket-id",
    type=int,
    help="Deliver and rsync the files for ALL cases connected to a ticket",
    required=True,
)
@click.option("-d", "--delivery-type", type=click.Choice(PIPELINE_ANALYSIS_OPTIONS), required=True)
@click.option("--dry-run", is_flag=True)
@click.pass_context
def deliver_ticket(
    context: click.Context,
    ticket_id: int,
    delivery_type: str,
    dry_run: bool,
):
    """Will first collect hard links in the customer inbox then
    concatenate fastq files if needed and finally send the folder
    from customer inbox hasta to the customer inbox on caesar.
    """
    cg_context: CGConfig = context.obj
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)
    is_upload_needed = deliver_ticket_api.check_if_upload_is_needed(ticket_id=ticket_id)
    if is_upload_needed:
        LOG.info("Delivering files to customer inbox on hasta")
        context.invoke(
            deliver_analysis, ticket_id=ticket_id, delivery_type=delivery_type, dry_run=dry_run
        )
    else:
        LOG.info("Files already delivered to customer inbox on hasta")
        return
    is_concatenation_needed = deliver_ticket_api.check_if_concatenation_is_needed(
        ticket_id=ticket_id
    )
    if is_concatenation_needed and delivery_type == "fastq":
        context.invoke(concatenate, ticket_id=ticket_id, dry_run=dry_run)
    context.invoke(rsync, ticket_id=ticket_id, dry_run=dry_run)
