"""Transfer CLI."""

import logging
from pathlib import Path

import rich_click as click

from cg.apps.lims import LimsAPI
from cg.apps.tb import TrailblazerAPI
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants import Workflow
from cg.constants.cli_options import DRY_RUN
from cg.constants.delivery import FileDeliveryOption
from cg.meta.transfer import PoolState, SampleState, TransferLims
from cg.models.cg_config import CGConfig
from cg.services.deliver_files import deliver_raw_data
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.factory import DeliveryServiceFactory
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.store.models import Analysis, Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)

DELIVERY_TYPE = click.option(
    "-d",
    "--delivery-type",
    multiple=False,
    type=click.Choice(choices=[option for option in FileDeliveryOption]),
    required=False,
    help="The delivery type to use. Overrides any delivery type from the case",
)
TICKET_ID_ARG = click.option("-t", "--ticket", type=str, required=True)


@click.group(name="transfer", context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_obj
def transfer_group():
    """Transfer results to the status interface."""
    LOG.debug("Running CG transfer")


@click.group(name="lims", context_settings=CLICK_CONTEXT_SETTINGS, hidden=True)
@click.pass_obj
def lims(context: CGConfig):
    """Transfer information about samples and pools from LIMS to the status interface."""
    lims_api: LimsAPI = context.lims_api
    status_db: Store = context.status_db
    context.meta_apis["transfer_lims_api"] = TransferLims(status=status_db, lims=lims_api)


transfer_group.add_command(lims)


@lims.command("samples", hidden=True)
@click.option(
    "--max-order-age",
    type=click.IntRange(min=1),
    default=None,
    help="Exclude samples with order dates older than N years. Must be greater than or equal to 1.",
)
@click.option(
    "-s", "--status", type=click.Choice(["received", "prepared", "delivered"]), default="received"
)
@click.option(
    "-i", "--include", type=click.Choice(["unset", "not-invoiced", "all"]), default="unset"
)
@click.option("--sample-id", help="Lims Submitted Sample id. use together with status.")
@click.pass_obj
def check_samples_in_lims(
    context: CGConfig, max_order_age: int | None, status: str, include: str, sample_id: str
):
    """Check if samples have been updated in LIMS."""
    transfer_api: TransferLims = context.meta_apis["transfer_lims_api"]
    transfer_api.transfer_samples(
        include=include,
        max_order_age=max_order_age,
        sample_id=sample_id,
        status_type=SampleState[status.upper()],
    )


@lims.command("pools", hidden=True)
@click.option("-s", "--status", type=click.Choice(["received", "delivered"]), default="delivered")
@click.pass_obj
def set_dates_of_pools(context: CGConfig, status: str):
    """
    Update pools with received_at or delivered_at dates from LIMS. Defaults to delivered if no
    option is provided.
    """
    transfer_api: TransferLims = context.meta_apis["transfer_lims_api"]
    transfer_api.transfer_pools(status_type=PoolState[status.upper()])


@transfer_group.command(name="rsync")
@click.pass_obj
@TICKET_ID_ARG
@DRY_RUN
def rsync(context: CGConfig, ticket: str, dry_run: bool):
    """The folder generated using the "cg transfer analysis" command will be
    rsynced with this function to the customers inbox on the delivery server
    """
    tb_api: TrailblazerAPI = context.trailblazer_api
    rsync_api: DeliveryRsyncService = context.delivery_rsync_service
    slurm_id = rsync_api.run_rsync_for_ticket(ticket=ticket, dry_run=dry_run)
    LOG.info(f"Rsync to the delivery server running as job {slurm_id}")
    rsync_api.add_to_trailblazer_api(
        tb_api=tb_api, slurm_job_id=slurm_id, ticket=ticket, dry_run=dry_run
    )


@transfer_group.command(
    name="case",
    help="Transfer all case files based on delivery type to the customer inbox on the HPC "
    "and start an Rsync job to clinical-delivery. "
    "NOTE: the dry-run flag will copy files to the customer inbox on Hasta, "
    "but will not perform the Rsync job.",
)
@click.pass_obj
@click.option(
    "-c",
    "--case-id",
    required=True,
    help="Transfer the files for a specific case.",
)
@DELIVERY_TYPE
@DRY_RUN
def transfer_case(
    context: CGConfig,
    case_id: str,
    delivery_type: FileDeliveryOption,
    dry_run: bool,
):
    """
    Transfer all case files based on delivery type to the customer inbox on the HPC
    """
    inbox: str = context.delivery_path
    service_builder: DeliveryServiceFactory = context.delivery_service_factory
    case: Case = context.status_db.get_case_by_internal_id(internal_id=case_id)
    if not case:
        LOG.error(f"Could not find case with id {case_id}")
        return
    delivery_service: DeliverFilesService = service_builder.build_delivery_service(
        case=case, delivery_type=delivery_type
    )
    delivery_service.deliver_files_for_case(
        case=case, delivery_base_path=Path(inbox), dry_run=dry_run
    )


@transfer_group.command(
    name="ticket",
    help="Transfer all case files for cases in a ticket based on delivery type to the customer"
    "inbox on the HPC and start an Rsync job to clinical-delivery. "
    "NOTE: the dry-run flag will copy files to the customer inbox on Hasta, "
    "but will not perform the Rsync job.",
)
@click.pass_obj
@TICKET_ID_ARG
@DELIVERY_TYPE
@DRY_RUN
def transfer_ticket(
    context: CGConfig,
    ticket: str,
    delivery_type: FileDeliveryOption,
    dry_run: bool,
):
    """
    Transfer all case files based on delivery type to the customer inbox on the HPC for cases
    connected to a ticket.
    """
    inbox: str = context.delivery_path
    service_builder: DeliveryServiceFactory = context.delivery_service_factory
    cases: list[Case] = context.status_db.get_cases_by_ticket_id(ticket_id=ticket)
    if not cases:
        LOG.error(f"Could not find case connected to ticket {ticket}")
        return
    delivery_service: DeliverFilesService = service_builder.build_delivery_service(
        case=cases[0], delivery_type=delivery_type
    )
    delivery_service.deliver_files_for_ticket(
        ticket_id=ticket, delivery_base_path=Path(inbox), dry_run=dry_run
    )


@transfer_group.command(
    name="sample",
    help="Transfer FASTQ or BAM files for a sample to the customer inbox on the HPC "
    "and start an Rsync job to clinical-delivery. "
    "NOTE: the dry-run flag will copy files to the customer inbox on Hasta, "
    "but will not perform the Rsync job.",
)
@click.pass_obj
@click.option(
    "-c",
    "--case-id",
    required=True,
    help="The case the sample is on.",
)
@click.option("-s", "--sample-id", required=True, help="Transfer the files for a specific sample.")
@click.option(
    "-d",
    "--delivery-type",
    required=True,
    help="The delivery type to use.",
    type=click.Choice(choices=["fastq", "bam"]),
)
@DRY_RUN
def transfer_sample_raw_data(
    context: CGConfig,
    case_id: str,
    sample_id: str,
    delivery_type: FileDeliveryOption,
    dry_run: bool,
):
    """
    Transfer FASTQ or BAM files for a single sample to the customer inbox on the HPC
    """
    inbox: str = context.delivery_path
    service_builder: DeliveryServiceFactory = context.delivery_service_factory
    case: Case = context.status_db.get_case_by_internal_id(internal_id=case_id)
    if not case:
        LOG.error(f"Could not find case with id {case_id}")
        return
    delivery_service: DeliverFilesService = service_builder.build_delivery_service(
        case=case, delivery_type=delivery_type
    )
    delivery_service.deliver_files_for_sample(
        case=case, sample_id=sample_id, delivery_base_path=Path(inbox), dry_run=dry_run
    )


@transfer_group.command(name="auto-raw-data")
@click.pass_obj
@DRY_RUN
def transfer_auto_raw_data(context: CGConfig, dry_run: bool):
    """
    Transfer all case files for the raw data workflow to the customer inbox on the HPC and start a
    Rsync job.
    1. get all cases with analysis type fastq that need to be delivered
    2. check if their upload has started
    3. if not, start the upload
    4. update the uploaded at field
    """
    service_builder: DeliveryServiceFactory = context.delivery_service_factory
    analyses: list[Analysis] = context.analysis_service.get_analyses_to_upload_for_workflow(
        workflow=Workflow.RAW_DATA
    )
    deliver_raw_data.deliver_analyses(
        analyses=analyses,
        status_db=context.status_db,
        delivery_path=Path(context.delivery_path),
        service_builder=service_builder,
        dry_run=dry_run,
    )
