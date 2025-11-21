"""Transfer CLI."""

import logging

import rich_click as click

from cg.apps.lims import LimsAPI
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.meta.transfer import PoolState, SampleState, TransferLims
from cg.models.cg_config import CGConfig
from cg.store.store import Store

LOG = logging.getLogger(__name__)


@click.group(name="transfer", context_settings=CLICK_CONTEXT_SETTINGS)
@click.pass_obj
def transfer_group(context: CGConfig):
    """Transfer results to the status interface."""
    lims_api: LimsAPI = context.lims_api
    status_db: Store = context.status_db
    context.meta_apis["transfer_lims_api"] = TransferLims(status=status_db, lims=lims_api)


@transfer_group.command("lims")
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


@transfer_group.command("pools")
@click.option("-s", "--status", type=click.Choice(["received", "delivered"]), default="delivered")
@click.pass_obj
def set_dates_of_pools(context: CGConfig, status: str):
    """
    Update pools with received_at or delivered_at dates from LIMS. Defaults to delivered if no
    option is provided.
    """
    transfer_api: TransferLims = context.meta_apis["transfer_lims_api"]
    transfer_api.transfer_pools(status_type=PoolState[status.upper()])
