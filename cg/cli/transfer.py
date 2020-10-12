import logging

import click

from cg.apps.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.stats import StatsAPI
from cg.meta import transfer as transfer_app
from cg.store import Store

log = logging.getLogger(__name__)


@click.group()
@click.pass_context
def transfer(context):
    """Transfer results to the status interface."""
    context.obj["status_db"] = Store(context.obj["database"])


@transfer.command()
@click.argument("flowcell_name")
@click.pass_context
def flowcell(context, flowcell_name):
    """Populate results from a flowcell."""
    stats_api = StatsAPI(context.obj)
    hk_api = HousekeeperAPI(context.obj)
    transfer_api = transfer_app.TransferFlowcell(context.obj["status_db"], stats_api, hk_api)
    new_record = transfer_api.transfer(flowcell_name)
    context.obj["status_db"].add_commit(new_record)
    click.echo(click.style(f"flowcell added: {new_record}", fg="green"))


@transfer.command()
@click.option(
    "-s", "--status", type=click.Choice(["received", "prepared", "delivered"]), default="received"
)
@click.option(
    "-i", "--include", type=click.Choice(["unset", "not-invoiced", "all"]), default="unset"
)
@click.option("--sample-id", help="Lims Submitted Sample id. use together with status.")
@click.pass_context
def lims(context, status, include, sample_id):
    """Check if samples have been updated in LIMS."""
    lims_api = LimsAPI(context.obj)
    transfer_api = transfer_app.TransferLims(context.obj["status_db"], lims_api)
    transfer_api.transfer_samples(transfer_app.SampleState[status.upper()], include, sample_id)


@transfer.command()
@click.option("-s", "--status", type=click.Choice(["received", "delivered"]), default="delivered")
@click.pass_context
def pools(context, status):
    """
    Update pools with received_at or delivered_at dates from LIMS. Defaults to delivered if no
    option is provided.
    """
    lims_api = LimsAPI(context.obj)
    transfer_api = transfer_app.TransferLims(context.obj["status_db"], lims_api)
    transfer_api.transfer_pools(transfer_app.PoolState[status.upper()])
