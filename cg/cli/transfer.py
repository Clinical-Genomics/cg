import logging

import click
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.transfer import PoolState, SampleState, TransferFlowcell, TransferLims
from cg.models.cg_config import CGConfig
from cg.store import Store, models

LOG = logging.getLogger(__name__)


@click.group(name="transfer")
@click.pass_obj
def transfer_group(context: CGConfig):
    """Transfer results to the status interface."""
    lims_api: LimsAPI = context.lims_api
    status_db: Store = context.status_db
    hk_api: HousekeeperAPI = context.housekeeper_api
    stats_api: StatsAPI = context.cg_stats_api
    context.meta_apis["transfer_flowcell_api"] = TransferFlowcell(
        db=status_db, stats_api=stats_api, hk_api=hk_api
    )
    context.meta_apis["transfer_lims_api"] = TransferLims(status=status_db, lims=lims_api)


@transfer_group.command()
@click.argument("flowcell_name")
@click.pass_obj
def flowcell(context: CGConfig, flowcell_name: str):
    """Populate results from a flowcell."""
    status_db: Store = context.status_db
    transfer_api = context.meta_apis["transfer_flowcell_api"]
    new_record: models.Flowcell = transfer_api.transfer(flowcell_name)
    status_db.add_commit(new_record)
    LOG.info("flowcell added: %s", new_record)


@transfer_group.command()
@click.option(
    "-s", "--status", type=click.Choice(["received", "prepared", "delivered"]), default="received"
)
@click.option(
    "-i", "--include", type=click.Choice(["unset", "not-invoiced", "all"]), default="unset"
)
@click.option("--sample-id", help="Lims Submitted Sample id. use together with status.")
@click.pass_obj
def lims(context: CGConfig, status: str, include: str, sample_id: str):
    """Check if samples have been updated in LIMS."""
    transfer_api: TransferLims = context.meta_apis["transfer_lims_api"]
    transfer_api.transfer_samples(
        status_type=SampleState[status.upper()], include=include, sample_id=sample_id
    )


@transfer_group.command()
@click.option("-s", "--status", type=click.Choice(["received", "delivered"]), default="delivered")
@click.pass_obj
def pools(context: CGConfig, status: str):
    """
    Update pools with received_at or delivered_at dates from LIMS. Defaults to delivered if no
    option is provided.
    """
    transfer_api: TransferLims = context.meta_apis["transfer_lims_api"]
    transfer_api.transfer_pools(status_type=PoolState[status.upper()])
