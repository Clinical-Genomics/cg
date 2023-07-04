"""Transfer CLI."""
import logging
import click

from pathlib import Path

from cg.apps.cgstats.stats import StatsAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.meta.transfer import PoolState, SampleState, TransferFlowCell, TransferLims
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Flowcell

LOG = logging.getLogger(__name__)


@click.group(name="transfer")
@click.pass_obj
def transfer_group(context: CGConfig):
    """Transfer results to the status interface."""
    lims_api: LimsAPI = context.lims_api
    status_db: Store = context.status_db
    hk_api: HousekeeperAPI = context.housekeeper_api
    stats_api: StatsAPI = context.cg_stats_api
    context.meta_apis["transfer_flow_cell_api"] = TransferFlowCell(
        db=status_db, stats_api=stats_api, hk_api=hk_api
    )
    context.meta_apis["transfer_lims_api"] = TransferLims(status=status_db, lims=lims_api)


@transfer_group.command("flow-cell")
@click.argument("flow-cell-id")
@click.option(
    "-d",
    "--flow-cell-dir",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="Path to demultiplexed flow cell output directory",
)
@click.option(
    "--store/--no-store", default=True, help="Store sample bundles of flow cell in Housekeeper"
)
@click.pass_obj
def populate_flow_cell(
    context: CGConfig, flow_cell_dir: str, flow_cell_id: str, store: bool = True
):
    """Populate results from a flow cell."""
    flow_cell_dir: Path = Path(flow_cell_dir)
    status_db: Store = context.status_db
    transfer_api: TransferFlowCell = context.meta_apis["transfer_flow_cell_api"]
    new_record: Flowcell = transfer_api.transfer(
        flow_cell_dir=flow_cell_dir, flow_cell_id=flow_cell_id, store=store
    )
    status_db.session.add(new_record)
    status_db.session.commit()
    LOG.info(f"flow cell added: {new_record}")


@transfer_group.command("lims")
@click.option(
    "-s", "--status", type=click.Choice(["received", "prepared", "delivered"]), default="received"
)
@click.option(
    "-i", "--include", type=click.Choice(["unset", "not-invoiced", "all"]), default="unset"
)
@click.option("--sample-id", help="Lims Submitted Sample id. use together with status.")
@click.pass_obj
def check_samples_in_lims(context: CGConfig, status: str, include: str, sample_id: str):
    """Check if samples have been updated in LIMS."""
    transfer_api: TransferLims = context.meta_apis["transfer_lims_api"]
    transfer_api.transfer_samples(
        status_type=SampleState[status.upper()], include=include, sample_id=sample_id
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
