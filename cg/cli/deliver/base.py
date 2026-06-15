"""CLI for delivering files with CG"""

import logging

import rich_click as click

from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.constants.cli_options import SIGNATURE
from cg.constants.delivery import FileDeliveryOption
from cg.models.cg_config import CGConfig
from cg.services.deliver_service import DeliverService

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


@click.group(context_settings=CLICK_CONTEXT_SETTINGS)
def deliver():
    """Deliver files with CG."""
    LOG.info("Running CG deliver")


@deliver.command(name="case", hidden=True)
@SIGNATURE
@click.argument("case_id", type=str, required=True)
@click.pass_obj
def deliver_case(config: CGConfig, case_id: str, signature: str):
    """
    Deliver a case by case ID.

    \b
    Performs:
        - Sends delivery message to connected ticket in Freshdesk
        - Marks latest analysis as delivered in Trailblazer
        - Marks sample as delivered if not delivered yet
        - Closes order in statusdb if all analyses on the order are delivered and all samples are marked as delivered
        - Closes ticket in Freshdesk if its status is open
    """
    freshdesk_client = FreshdeskClient(
        base_url=config.freshdesk.base_url, api_key=config.freshdesk.api_key
    )
    deliver_service = DeliverService(
        freshdesk_client=freshdesk_client,
        status_db=config.status_db,
        trailblazer_api=config.trailblazer_api,
    )
    deliver_service.deliver_case(case_id=case_id, signature=signature)
    config.status_db.commit_to_store()


@deliver.command(name="order", hidden=True)
@SIGNATURE
@click.option(
    "--ticket-id",
    "-t",
    type=int,
    required=True,
    help="Freshdesk ticket id corresponding to the order",
)
@click.pass_obj
def deliver_order(config: CGConfig, signature: str, ticket_id: int):
    """
    Deliver all analysis ready to be delivered in an order by ticket_id.

    \b
    Performs:
        - Sends delivery message to connected ticket in Freshdesk
        - Marks analyses as delivered in Trailblazer
        - If applicable marks sample as delivered
        - If applicable closes order in statusdb
        - If applicable closes ticket in Freshdesk
    """
    freshdesk_client = FreshdeskClient(
        base_url=config.freshdesk.base_url, api_key=config.freshdesk.api_key
    )
    deliver_service = DeliverService(
        freshdesk_client=freshdesk_client,
        status_db=config.status_db,
        trailblazer_api=config.trailblazer_api,
    )
    deliver_service.deliver_order(signature=signature, ticket_id=ticket_id)
    config.status_db.commit_to_store()


@deliver.command(name="all-available", hidden=True)
@click.pass_obj
def deliver_all_available(config: CGConfig):
    """
    Deliver all cases that have an analysis ready to be delivered in trailblazer.

    \b
    Performs:
        - Sends delivery message to connected ticket in Freshdesk
        - Marks analysis as delivered in Trailblazer
        - Marks sample as delivered if not delivered yet
        - Closes order in statusdb if all analyses on the order are delivered and all samples are marked as delivered
        - Closes ticket in Freshdesk if its status is open
    """
    freshdesk_client = FreshdeskClient(
        base_url=config.freshdesk.base_url, api_key=config.freshdesk.api_key
    )
    deliver_service = DeliverService(
        freshdesk_client=freshdesk_client,
        status_db=config.status_db,
        trailblazer_api=config.trailblazer_api,
    )
    if not deliver_service.deliver_all_available():
        raise click.Abort()
