"""Transfer CLI."""

import logging
from datetime import datetime

import rich_click as click

from cg.apps.lims import LimsAPI
from cg.cli.utils import CLICK_CONTEXT_SETTINGS
from cg.meta.transfer import PoolState, SampleState, TransferLims
from cg.models.cg_config import CGConfig
from cg.store.store import Store
from cg.utils.date import get_date_days_ago

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
    "--order-age-cutoff",
    type=int,
    help="Exclude samples with order dates older than N years. If not set, include all samples.",
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
    context: CGConfig, order_age_cutoff: int, status: str, include: str, sample_id: str
):
    """Check if samples have been updated in LIMS."""
    order_date_cutoff: datetime = get_date_days_ago(order_age_cutoff * 365)
    transfer_api: TransferLims = context.meta_apis["transfer_lims_api"]
    transfer_api.transfer_samples(
        order_date_cutoff=order_date_cutoff,
        status_type=SampleState[status.upper()],
        include=include,
        sample_id=sample_id,
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
