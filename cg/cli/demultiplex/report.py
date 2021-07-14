import logging
from pathlib import Path
from typing import Dict

import click

from cg.apps.cgstats.parsers.conversion_stats import ConversionStats
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.demux_report import create_demux_report
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.exc import FlowcellError
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


@click.command(name="report")
@OPTION_BCL_CONVERTER
@click.argument("flowcell-name")
@click.pass_obj
def create_report_cmd(context: CGConfig, flowcell_name: str, bcl_converter: str):
    """Generate a demux report and print to stdout"""
    LOG.info("Check demuxed flowcell %s", flowcell_name)
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    try:
        flowcell: Flowcell = Flowcell(flowcell_path=demultiplex_api.run_dir / flowcell_name)
    except FlowcellError:
        raise click.Abort
    demux_stats_files: Dict = demultiplex_api.get_demux_stats_files(
        flowcell=flowcell, bcl_converter=bcl_converter
    )
    demux_results: DemuxResults = DemuxResults(
        demux_dir=demultiplex_api.out_dir / flowcell_name,
        flowcell=flowcell,
        bcl_converter=bcl_converter,
        demux_stats_files=demux_stats_files,
    )
    conversion_stats: Path = demux_results.conversion_stats_path
    if not conversion_stats.exists():
        LOG.warning("Could not find conversion stats file %s", conversion_stats)
        raise click.Abort
    report = create_demux_report(
        conversion_stats=ConversionStats(demux_results.conversion_stats_path)
    )
    click.echo("\n".join(report))
