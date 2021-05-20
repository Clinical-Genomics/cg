import logging
from pathlib import Path

import click
from cg.apps.cgstats.parsers.conversion_stats import ConversionStats
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.demux_report import create_demux_report
from cg.exc import FlowcellError
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


@click.command(name="report")
@click.argument("flowcell-name")
@click.pass_obj
def create_report_cmd(context: CGConfig, flowcell_name: str):
    """Generate a demux report and print to stdout"""
    LOG.info("Check demuxed flowcell %s", flowcell_name)
    demux_api: DemultiplexingAPI = context.demultiplex_api
    try:
        flowcell: Flowcell = Flowcell(flowcell_path=demux_api.run_dir / flowcell_name)
    except FlowcellError:
        raise click.Abort
    demux_results: DemuxResults = DemuxResults(
        demux_dir=demux_api.out_dir / flowcell_name, flowcell=flowcell
    )
    conversion_stats: Path = demux_results.conversion_stats_path
    if not conversion_stats.exists():
        LOG.warning("Could not find conversion stats file %s", conversion_stats)
        raise click.Abort
    report = create_demux_report(
        conversion_stats=ConversionStats(demux_results.conversion_stats_path)
    )
    click.echo("\n".join(report))
