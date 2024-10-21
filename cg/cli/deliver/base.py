"""CLI for delivering files with CG"""

import logging
from pathlib import Path

import click

from cg.apps.tb import TrailblazerAPI
from cg.cli.deliver.utils import deliver_raw_data_for_analyses
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants import Workflow
from cg.constants.cli_options import DRY_RUN
from cg.constants.delivery import FileDeliveryOption
from cg.models.cg_config import CGConfig
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.deliver_files_service.deliver_files_service_factory import (
    DeliveryServiceFactory,
)
from cg.services.deliver_files.rsync.service import (
    DeliveryRsyncService,
)
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)

DELIVERY_TYPE = click.option(
    "-d",
    "--delivery-type",
    multiple=False,
    type=click.Choice(choices=[option for option in FileDeliveryOption]),
    required=False,
)
TICKET_ID_ARG = click.option("-t", "--ticket", type=str, required=True)


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def deliver():
    """Deliver files with CG."""
    LOG.info("Running CG deliver")


@deliver.command(name="rsync")
@click.pass_obj
@TICKET_ID_ARG
@DRY_RUN
def rsync(context: CGConfig, ticket: str, dry_run: bool):
    """The folder generated using the "cg deliver analysis" command will be
    rsynced with this function to the customers inbox on the delivery server
    """
    tb_api: TrailblazerAPI = context.trailblazer_api
    rsync_api: DeliveryRsyncService = context.delivery_rsync_service
    slurm_id = rsync_api.run_rsync_for_ticket(ticket=ticket, dry_run=dry_run)
    LOG.info(f"Rsync to the delivery server running as job {slurm_id}")
    rsync_api.add_to_trailblazer_api(
        tb_api=tb_api, slurm_job_id=slurm_id, ticket=ticket, dry_run=dry_run
    )


@deliver.command(
    name="case",
    help="Deliver all case files based on delivery type to the customer inbox on the HPC "
    "and start an Rsync job to clinical-delivery. "
    "NOTE: the dry-run flag will copy files to the customer inbox on Hasta, "
    "but will not perform the Rsync job.",
)
@click.pass_obj
@click.option(
    "-c",
    "--case-id",
    required=True,
    help="Deliver the files for a specific case.",
)
@DELIVERY_TYPE
@DRY_RUN
def deliver_case(
    context: CGConfig,
    case_id: str,
    delivery_type: FileDeliveryOption,
    dry_run: bool,
):
    """
    Deliver all case files based on delivery type to the customer inbox on the HPC
    """
    inbox: str = context.delivery_path
    service_builder: DeliveryServiceFactory = context.delivery_service_factory
    case: Case = context.status_db.get_case_by_internal_id(internal_id=case_id)
    if not case:
        LOG.error(f"Could not find case with id {case_id}")
        return
    delivery_service: DeliverFilesService = service_builder.build_delivery_service(
        delivery_type=delivery_type if delivery_type else case.data_delivery,
        workflow=case.data_analysis,
    )
    delivery_service.deliver_files_for_case(
        case=case, delivery_base_path=Path(inbox), dry_run=dry_run
    )


@deliver.command(
    name="ticket",
    help="Deliver all case files for cases in a ticket based on delivery type to the customer inbox on the HPC "
    "and start an Rsync job to clinical-delivery. "
    "NOTE: the dry-run flag will copy files to the customer inbox on Hasta, "
    "but will not perform the Rsync job.",
)
@click.pass_obj
@TICKET_ID_ARG
@DELIVERY_TYPE
@DRY_RUN
def deliver_ticket(
    context: CGConfig,
    ticket: str,
    delivery_type: FileDeliveryOption,
    dry_run: bool,
):
    """
    Deliver all case files based on delivery type to the customer inbox on the HPC for cases connected to a ticket.
    """
    inbox: str = context.delivery_path
    service_builder: DeliveryServiceFactory = context.delivery_service_factory
    cases: list[Case] = context.status_db.get_cases_by_ticket_id(ticket_id=ticket)
    if not cases:
        LOG.error(f"Could not find case connected to ticket {ticket}")
        return
    delivery_service: DeliverFilesService = service_builder.build_delivery_service(
        delivery_type=delivery_type if delivery_type else cases[0].data_delivery,
        workflow=cases[0].data_analysis,
    )
    delivery_service.deliver_files_for_ticket(
        ticket_id=ticket, delivery_base_path=Path(inbox), dry_run=dry_run
    )


@deliver.command(
    name="sample",
    help="Deliver fastq or bam files for a sample to the customer inbox on the HPC "
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
@click.option("-s", "--sample-id", required=True, help="Deliver the files for a specific sample.")
@click.option(
    "-d",
    "--delivery-type",
    required=True,
    help="The delivery type to use.",
    type=click.Choice(choices=["fastq", "bam"]),
)
@DRY_RUN
def deliver_sample_raw_data(
    context: CGConfig,
    case_id: str,
    sample_id: str,
    delivery_type: FileDeliveryOption,
    dry_run: bool,
):
    """
    Deliver fastq or bam files for a single sample to the customer inbox on the HPC
    """
    inbox: str = context.delivery_path
    service_builder: DeliveryServiceFactory = context.delivery_service_factory
    case: Case = context.status_db.get_case_by_internal_id(internal_id=case_id)
    if not case:
        LOG.error(f"Could not find case with id {case_id}")
        return
    delivery_service: DeliverFilesService = service_builder.build_delivery_service(
        delivery_type=delivery_type,
        workflow=case.data_analysis,
    )
    delivery_service.deliver_files_for_sample(
        case=case, sample_id=sample_id, delivery_base_path=Path(inbox), dry_run=dry_run
    )


@deliver.command(name="auto-raw-data")
@click.pass_obj
@DRY_RUN
def deliver_auto_raw_data(context: CGConfig, dry_run: bool):
    """
    Deliver all case files for the raw data workflow to the customer inbox on the HPC and start a Rsync job.
    1. get all cases with analysis type fastq that need to be delivered
    2. check if their upload has started
    3. if not, start the upload
    4. update the uploaded at field
    """
    """Starts upload of all not previously uploaded cases with analysis type fastq to
       clinical-delivery."""
    service_builder: DeliveryServiceFactory = context.delivery_service_factory
    analyses: list[Analysis] = context.analysis_service.get_analyses_to_upload_for_workflow(
        workflow=Workflow.RAW_DATA
    )
    deliver_raw_data_for_analyses(
        analyses=analyses,
        status_db=context.status_db,
        delivery_path=Path(context.delivery_path),
        service_builder=service_builder,
        dry_run=dry_run,
    )
