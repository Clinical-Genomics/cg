"""CLI for delivering files with CG"""

import logging
from pathlib import Path

import click

from cg.apps.tb import TrailblazerAPI
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN
from cg.constants.delivery import PIPELINE_ANALYSIS_OPTIONS, PIPELINE_ANALYSIS_TAG_MAP
from cg.meta.deliver import DeliverAPI, DeliverTicketAPI
from cg.meta.rsync.rsync_api import RsyncAPI
from cg.models.cg_config import CGConfig
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)

DELIVERY_TYPE = click.option(
    "-d",
    "--delivery-type",
    multiple=True,
    type=click.Choice(PIPELINE_ANALYSIS_OPTIONS),
    required=True,
)
FORCE_ALL = click.option(
    "--force-all",
    help=(
        "Force delivery of all sample files "
        "- disregarding of amount of reads or previous deliveries"
    ),
    is_flag=True,
)
TICKET_ID_ARG = click.argument("ticket", type=str, required=True)

IGNORE_MISSING_BUNDLES = click.option(
    "-i",
    "--ignore-missing-bundles",
    help="Ignore errors due to missing case bundles",
    is_flag=True,
    default=False,
)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def deliver():
    """Deliver files with CG."""
    LOG.info("Running CG deliver")


@deliver.command(name="analysis")
@DRY_RUN
@DELIVERY_TYPE
@click.option("-c", "--case-id", help="Deliver the files for a specific case")
@click.option(
    "-t", "--ticket", type=str, help="Deliver the files for ALL cases connected to a ticket"
)
@FORCE_ALL
@IGNORE_MISSING_BUNDLES
@click.pass_obj
def deliver_analysis(
    context: CGConfig,
    case_id: str | None,
    ticket: str | None,
    delivery_type: list[str],
    dry_run: bool,
    force_all: bool,
    ignore_missing_bundles: bool,
):
    """Deliver analysis files to customer inbox

    Files can be delivered either on case level or for all cases connected to a ticket.
    Any of those needs to be specified.
    """
    if not (case_id or ticket):
        LOG.info("Please provide a case-id or ticket-id")
        return

    inbox: str = context.delivery_path
    if not inbox:
        LOG.info("Please specify the root path for where files should be delivered")
        return

    status_db: Store = context.status_db
    for delivery in delivery_type:
        deliver_api = DeliverAPI(
            store=status_db,
            hk_api=context.housekeeper_api,
            case_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery]["case_tags"],
            sample_tags=PIPELINE_ANALYSIS_TAG_MAP[delivery]["sample_tags"],
            project_base_path=Path(inbox),
            delivery_type=delivery,
            force_all=force_all,
            ignore_missing_bundles=ignore_missing_bundles,
            fastq_file_service=FastqConcatenationService(),
        )
        deliver_api.set_dry_run(dry_run)
        cases: list[Case] = []
        if case_id:
            case_obj: Case = status_db.get_case_by_internal_id(internal_id=case_id)
            if not case_obj:
                LOG.warning(f"Could not find case {case_id}")
                return
            cases.append(case_obj)
        else:
            cases: list[Case] = status_db.get_cases_by_ticket_id(ticket_id=ticket)
            if not cases:
                LOG.warning(f"Could not find cases for ticket {ticket}")
                return

        for case_obj in cases:
            deliver_api.deliver_files(case_obj=case_obj)


@deliver.command(name="rsync")
@DRY_RUN
@TICKET_ID_ARG
@click.pass_obj
def rsync(context: CGConfig, ticket: str, dry_run: bool):
    """The folder generated using the "cg deliver analysis" command will be
    rsynced with this function to the customers inbox on the delivery server
    """
    tb_api: TrailblazerAPI = context.trailblazer_api
    rsync_api: RsyncAPI = RsyncAPI(config=context)
    slurm_id = rsync_api.run_rsync_on_slurm(ticket=ticket, dry_run=dry_run)
    LOG.info(f"Rsync to the delivery server running as job {slurm_id}")
    rsync_api.add_to_trailblazer_api(
        tb_api=tb_api, slurm_job_id=slurm_id, ticket=ticket, dry_run=dry_run
    )


@deliver.command(name="concatenate")
@DRY_RUN
@TICKET_ID_ARG
@click.pass_context
def concatenate(context: click.Context, ticket: str, dry_run: bool):
    """The fastq files in the folder generated using "cg deliver analysis"
    will be concatenated into one forward and one reverse fastq file
    """
    cg_context: CGConfig = context.obj
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)
    deliver_ticket_api.concatenate_fastq_files(ticket=ticket, dry_run=dry_run)


@deliver.command(name="ticket")
@DELIVERY_TYPE
@DRY_RUN
@FORCE_ALL
@IGNORE_MISSING_BUNDLES
@click.option(
    "-t",
    "--ticket",
    type=str,
    help="Deliver and rsync the files for ALL cases connected to a ticket",
    required=True,
)
@click.pass_context
def deliver_ticket(
    context: click.Context,
    delivery_type: list[str],
    dry_run: bool,
    force_all: bool,
    ticket: str,
    ignore_missing_bundles: bool,
):
    """Will first collect hard links in the customer inbox then
    concatenate fastq files if needed and finally send the folder
    from customer inbox hasta to the customer inbox on the delivery server
    """
    cg_context: CGConfig = context.obj
    deliver_ticket_api = DeliverTicketAPI(config=cg_context)
    is_upload_needed = deliver_ticket_api.check_if_upload_is_needed(ticket=ticket)
    if is_upload_needed or force_all:
        LOG.info("Delivering files to customer inbox on the HPC")
        context.invoke(
            deliver_analysis,
            delivery_type=delivery_type,
            dry_run=dry_run,
            force_all=force_all,
            ticket=ticket,
            ignore_missing_bundles=ignore_missing_bundles,
        )
    else:
        LOG.info("Files already delivered to customer inbox on the HPC")
        return

    deliver_ticket_api.report_missing_samples(ticket=ticket, dry_run=dry_run)
    context.invoke(rsync, ticket=ticket, dry_run=dry_run)
