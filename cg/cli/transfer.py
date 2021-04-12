import logging

import click

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.stats import StatsAPI
from cg.meta.transfer import TransferFlowcell, TransferLims, SampleState, PoolState
from cg.store import Store
from cg.store import models

LOG = logging.getLogger(__name__)


@click.group(name="transfer")
def transfer_group():
    """Transfer results to the status interface."""
    pass


@transfer_group.command()
@click.argument("flowcell_name")
@click.pass_context
def flowcell(context: click.Context, flowcell_name: str):
    """Populate results from a flowcell."""
    stats_api = StatsAPI(context.obj)
    hk_api: HousekeeperAPI = context.obj["housekeeper_api"]
    status_db: Store = context.obj["status_db"]
    transfer_api = TransferFlowcell(db=status_db, stats_api=stats_api, hk_api=hk_api)
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
@click.pass_context
def lims(context: click.Context, status: str, include: str, sample_id: str):
    """Check if samples have been updated in LIMS."""
    lims_api = LimsAPI(context.obj)
    status_db: Store = context.obj["status_db"]
    transfer_api = TransferLims(status=status_db, lims=lims_api)
    transfer_api.transfer_samples(
        status_type=SampleState[status.upper()], include=include, sample_id=sample_id
    )


@transfer_group.command()
@click.option("-s", "--status", type=click.Choice(["received", "delivered"]), default="delivered")
@click.pass_context
def pools(context, status):
    """
    Update pools with received_at or delivered_at dates from LIMS. Defaults to delivered if no
    option is provided.
    """
    lims_api = LimsAPI(context.obj)
    status_db: Store = context.obj["status_db"]
    transfer_api = TransferLims(status=status_db, lims=lims_api)
    transfer_api.transfer_pools(status_type=PoolState[status.upper()])
