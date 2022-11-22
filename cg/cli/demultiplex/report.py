import logging
from pathlib import Path

import click
from cg.apps.cgstats.parsers.conversion_stats import ConversionStats
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.demux_report import create_demux_report
from cg.exc import FlowCellError
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flow_cell import FlowCell

LOG = logging.getLogger(__name__)


@click.command(name="report")
@click.argument("flow-cell-name")
@click.pass_obj
def create_report_cmd(context: CGConfig, flow_cell_name: str):
    """Generate a demux report and print to stdout."""
    LOG.info(f"Check demuxed flowcell {flow_cell_name}")
    demux_api: DemultiplexingAPI = context.demultiplex_api
    try:
        flow_cell: FlowCell = FlowCell(flow_cell_path=Path(demux_api.run_dir, flow_cell_name))
    except FlowCellError as error:
        raise click.Abort from error
    demux_results: DemuxResults = DemuxResults(
        demux_dir=Path(demux_api.out_dir, flow_cell_name, flow_cell=flow_cell)
    )
    conversion_stats: Path = demux_results.conversion_stats_path
    if not conversion_stats.exists():
        LOG.warning(f"Could not find conversion stats file {conversion_stats}")
        raise click.Abort
    report = create_demux_report(
        conversion_stats=ConversionStats(demux_results.conversion_stats_path)
    )
    click.echo("\n".join(report))
