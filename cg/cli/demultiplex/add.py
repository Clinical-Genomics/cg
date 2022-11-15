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
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.exc import FlowCellError
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingNovaseqAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCell

LOG = logging.getLogger(__name__)


@click.command(name="add")
@OPTION_BCL_CONVERTER
@click.argument("flow-cell-name")
@click.pass_obj
def add_flow_cell_cmd(context: CGConfig, flow_cell_name: str, bcl_converter: str):
    """Add a flow cell to the cgstats database."""
    stats_api: StatsAPI = context.cg_stats_api
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    flow_cell_run_path: Path = Path(demultiplex_api.run_dir, flow_cell_name)
    if not flow_cell_run_path.exists():
        LOG.warning(f"Could not find flow cell path {flow_cell_run_path}")
        raise click.Abort
    demux_results_path: Path = Path(demultiplex_api.out_dir, flow_cell_name)
    if not demux_results_path.exists():
        LOG.warning(f"Could not find demultiplex result path {demux_results_path}")
        raise click.Abort
    try:
        flow_cell: FlowCell = FlowCell(
            flow_cell_path=flow_cell_run_path, bcl_converter=bcl_converter
        )
    except FlowCellError as error:
        raise click.Abort from error
    demux_results: DemuxResults = DemuxResults(
        demux_dir=demux_results_path, flow_cell=flow_cell, bcl_converter=bcl_converter
    )
    create_novaseq_flowcell(manager=stats_api, demux_results=demux_results)


@click.command(name="select")
@click.argument("flow-cell-id")
@click.option("--project", help="Name of project to fetch data for")
@click.pass_obj
def select_project_cmd(context: CGConfig, flow_cell_id: str, project: Optional[str]):
    """Select a flow cell to fetch statistics from"""
    # Need to instantiate API
    post_processing_api = DemuxPostProcessingNovaseqAPI(config=context)
    report_content: List[str] = post_processing_api.get_report_data(
        flow_cell_id=flow_cell_id, project_name=project
    )

    click.echo("\t".join(STATS_HEADER))
    if not report_content:
        LOG.warning(f"Could not find any samples for flow cell {flow_cell_id}, project {project}")
        return
    for report_line in report_content:
        click.echo(report_line)
