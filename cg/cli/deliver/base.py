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
@click.option("--cron", is_flag=True)
@click.pass_obj
def deliver_ticket(
    context: CGConfig,
    ticket_id: int,
    delivery_type: str,
    dry_run: bool,
    cron: bool,
):
    """Will first collect hard links in the customer inbox then
    concatenate fastq files if needed and finally send the folder
    from customer inbox hasta to the customer inbox on caesar.
    """
    is_upload_needed = check_if_upload_is_needed()
    if is_upload_needed:
        deliver_analysis(
            context=context, ticket_id=ticket_id, delivery_type=delivery_type, dry_run=dry_run
        )
    else:
        return
    is_concatenation_needed = check_if_concatenation_is_needed()
    if is_concatenation_needed:
        run_mutant_toolbox_concatenate()
    update_uploaded_started_at()
    rsync(context=context, ticket_id=ticket_id, dry_run=dry_run)
    update_uploaded_at()



    is_uploaded = check_if_uploaded()
    if is_uploaded and cron:
        LOG.debug("The folder is already uploaded")
        return
    if is_uploaded:
        customer_inbox = get_customer_inbox()
        LOG.info("Folder: %s already exist", customer_inbox)
        if input("This has already been uploaded, do you want to remove the folder from customer inbox and re-upload? ") != 'y':
            break

    remove_customer_inbox()



# Check if uploaded, stop if it is
# Check if inbox is there, and if so delete it
# run deliver_analysis()
# find what app-tag it is
# find what ordered at date it is
# run mutant tool box concatenate
# Update uploaded started at
# run cg rsync
# update uploaded at

