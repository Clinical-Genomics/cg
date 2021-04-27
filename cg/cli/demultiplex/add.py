import logging
from pathlib import Path

import alchy
import click
from cg.apps.cgstats.crud.create import create_novaseq_flowcell
from cg.apps.cgstats.crud.find import project_sample_stats
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


@click.command(name="add")
@click.argument("flowcell-id")
@click.pass_obj
def add_flowcell_cmd(context: CGConfig, flowcell_id: str):
    """Add a flowcell to the cgstats database"""
    stats_api: StatsAPI = context.cg_stats_api
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    flowcell_run_path: Path = demultiplex_api.run_dir / flowcell_id
    if not flowcell_run_path.exists():
        LOG.warning("Could not find flowcell path %s", flowcell_run_path)
        raise click.Abort
    demux_results_path: Path = demultiplex_api.out_dir / flowcell_id
    if not demux_results_path.exists():
        LOG.warning("Could not find demultiplex result path %s", demux_results_path)
        raise click.Abort
    flowcell: Flowcell = Flowcell(flowcell_path=flowcell_run_path)
    demux_results: DemuxResults = DemuxResults(demux_dir=demux_results_path, flowcell=flowcell)
    create_novaseq_flowcell(manager=stats_api, demux_results=demux_results)


@click.command(name="select")
@click.argument("flowcell-id")
@click.option("--project", help="Name of project to fetch data for", required=True)
@click.pass_obj
def select_project_cmd(context: CGConfig, flowcell_id: str, project: str):
    """Select a flowcell to fetch statistics from"""
    stats_api: StatsAPI = context.cg_stats_api
    query: alchy.Query = project_sample_stats(
        manager=stats_api, flowcell=flowcell_id, project_name=project
    )
    stats_header = [
        "sample",
        "Flowcell",
        "Lanes",
        "readcounts/lane",
        "sum_readcounts",
        "yieldMB/lane",
        "sum_yield",
        "%Q30",
        "MeanQscore",
    ]
    click.echo("\t".join(stats_header))
    for line in query:
        click.echo(
            "\t".join(
                str(s)
                for s in [
                    line.samplename,
                    line.flowcellname,
                    line.lanes,
                    line.reads,
                    line.readsum,
                    line.yld,
                    line.yieldsum,
                    line.q30,
                    line.meanq,
                ]
            )
        )
