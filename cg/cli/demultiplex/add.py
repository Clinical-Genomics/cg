"""Commands to mimic the behaviour from cgstats.

This is a way to interact with cgstats manually. In automated production these commands will not be run.
"""
import logging
from pathlib import Path
from typing import List, Optional

import click
from cg.apps.cgstats.crud.create import create_novaseq_flowcell
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.constants.cgstats import STATS_HEADER
from cg.exc import FlowcellError
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
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
    try:
        flowcell: Flowcell = Flowcell(flowcell_path=flowcell_run_path)
    except FlowcellError:
        raise click.Abort
    demux_results: DemuxResults = DemuxResults(demux_dir=demux_results_path, flowcell=flowcell)
    create_novaseq_flowcell(manager=stats_api, demux_results=demux_results)


@click.command(name="select")
@click.argument("flowcell-id")
@click.option("--project", help="Name of project to fetch data for")
@click.pass_obj
def select_project_cmd(context: CGConfig, flowcell_id: str, project: Optional[str]):
    """Select a flowcell to fetch statistics from"""
    # Need to instantiate API
    post_processing_api = DemuxPostProcessingAPI(config=context)
    report_content: List[str] = post_processing_api.get_report_data(
        flowcell_id=flowcell_id, project_name=project
    )

    click.echo("\t".join(STATS_HEADER))
    if not report_content:
        LOG.warning("Could not find any samples for flowcell %s, project %s", flowcell_id, project)
        return
    for report_line in report_content:
        click.echo(report_line)
