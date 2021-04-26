import click
from cg.apps.cgstats.stats import StatsAPI
from cg.models.cg_config import CGConfig


@click.command(name="add")
@click.argument("flowcell-id")
@click.pass_obj
def add_flowcell_cmd(context: CGConfig, flowcell_id: str):
    """Add a flowcell to the cgstats database"""
    stats_api: StatsAPI = context.cg_stats_api
