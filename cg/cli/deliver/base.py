"""CLI for delivering files with CG"""

import logging
from pathlib import Path

import click

from cg.apps.tb import TrailblazerAPI
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.constants.cli_options import DRY_RUN
from cg.constants.delivery import PIPELINE_ANALYSIS_OPTIONS
from cg.meta.rsync.rsync_api import RsyncAPI
from cg.models.cg_config import CGConfig
from cg.services.file_delivery.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.file_delivery.deliver_files_service.deliver_files_service_factory import (
    DeliveryServiceFactory,
)
from cg.store.models import Case

LOG = logging.getLogger(__name__)

DELIVERY_TYPE = click.option(
    "-d",
    "--delivery-type",
    multiple=True,
    type=click.Choice(PIPELINE_ANALYSIS_OPTIONS),
    required=True,
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
    rsync_api: RsyncAPI = RsyncAPI(config=context)
    slurm_id = rsync_api.run_rsync_on_slurm(ticket=ticket, dry_run=dry_run)
    LOG.info(f"Rsync to the delivery server running as job {slurm_id}")
    rsync_api.add_to_trailblazer_api(
        tb_api=tb_api, slurm_job_id=slurm_id, ticket=ticket, dry_run=dry_run
    )


@deliver.command(name="case")
@click.pass_obj
@click.option(
    "-c",
    "--case-id",
    required=True,
    help="Deliver the files for a specific case",
)
@DRY_RUN
def deliver_case(
    context: CGConfig,
    case_id: str,
    dry_run: bool,
):
    """
    Deliver all case files based on delivery type to the customer inbox on the HPC
    """
    inbox: str = context.delivery_path
    rsync_api: RsyncAPI = RsyncAPI(config=context)
    service_builder = DeliveryServiceFactory(
        store=context.status_db,
        hk_api=context.housekeeper_api,
        tb_service=context.trailblazer_api,
        rsync_service=rsync_api,
    )
    case: Case = context.status_db.get_case_by_internal_id(internal_id=case_id)
    if not case:
        LOG.error(f"Could not find case with id {case_id}")
        return
    delivery_service: DeliverFilesService = service_builder.build_delivery_service(
        delivery_type=case.data_delivery,
        workflow=case.workflow,
    )
    delivery_service.deliver_files_for_case(
        case=case, delivery_base_path=Path(inbox), dry_run=dry_run
    )


@deliver.command(name="ticket")
@click.pass_obj
@TICKET_ID_ARG
@DRY_RUN
def deliver_ticket(
    context: CGConfig,
    ticket: str,
    dry_run: bool,
):
    """
    Deliver all case files based on delivery type to the customer inbox on the HPC for cases connected to a ticket.
    """
    inbox: str = context.delivery_path
    rsync_api: RsyncAPI = RsyncAPI(config=context)
    service_builder = DeliveryServiceFactory(
        store=context.status_db,
        hk_api=context.housekeeper_api,
        tb_service=context.trailblazer_api,
        rsync_service=rsync_api,
    )

    cases: list[Case] = context.status_db.get_cases_by_ticket_id(ticket_id=ticket)
    if not cases:
        LOG.error(f"Could not find case connected to ticket {ticket}")
        return
    delivery_service: DeliverFilesService = service_builder.build_delivery_service(
        delivery_type=cases[0].data_delivery,
        workflow=cases[0].workflow,
    )
    delivery_service.deliver_files_for_ticket(
        ticket_id=ticket, delivery_base_path=Path(inbox), dry_run=dry_run
    )
