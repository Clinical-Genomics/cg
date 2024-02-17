"""CLI for delivering files with CG"""

import logging
import click

from cg.apps.tb import TrailblazerAPI
from cg.constants.delivery import PIPELINE_ANALYSIS_OPTIONS
from cg.meta.deliver import DeliveryAPI
from cg.meta.deliver_ticket import DeliverTicketAPI
from cg.meta.rsync.rsync_api import RsyncAPI
from cg.models.cg_config import CGConfig

LOG = logging.getLogger(__name__)

DRY_RUN = click.option("--dry-run", is_flag=True)
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


@click.group()
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
    """Deliver analysis files to customer inbox.
    Files can be delivered either on case level or for all cases connected to a ticket.
    """
    if not (case_id or ticket):
        LOG.info("Please provide a case-id or ticket-id")
        return

    delivery_api: DeliveryAPI = context.delivery_api

    delivery_api.dry_run = dry_run
    delivery_api.deliver_failed_samples = force_all
    delivery_api.ignore_missing_bundles = ignore_missing_bundles

    for delivery in delivery_type:
        delivery_api.deliver(case_id=case_id, ticket=ticket, pipeline=delivery)


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
    deliver_ticket_api.concatenate(ticket=ticket, dry_run=dry_run)


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
    is_concatenation_needed: bool = deliver_ticket_api.check_if_concatenation_is_needed(
        ticket=ticket
    )
    if is_concatenation_needed and "fastq" in delivery_type:
        context.invoke(concatenate, ticket=ticket, dry_run=dry_run)
    deliver_ticket_api.report_missing_samples(ticket=ticket, dry_run=dry_run)
    context.invoke(rsync, ticket=ticket, dry_run=dry_run)
