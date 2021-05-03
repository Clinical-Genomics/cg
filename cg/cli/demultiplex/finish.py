"""Commands to finish up after a demultiplex run"""
import logging
from pathlib import Path

import click
from cg.apps.cgstats.stats import StatsAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.meta.demultiplex.demux_post_processing import DemuxPostProcessingAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.demux_results import DemuxResults
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


@click.group(name="finish")
def finish_group():
    """Finish up after demultiplexing"""
    pass


@finish_group.command(name="all")
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def finish_all_cmd(context: CGConfig, dry_run: bool):
    """Command to post process all demultiplexed flowcells"""
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    stats_api: StatsAPI = context.cg_stats_api
    demux_post_processing_api = DemuxPostProcessingAPI(stats_api=stats_api)
    demuxed_flowcells_dir: Path = demultiplex_api.out_dir
    for flowcell_dir in demuxed_flowcells_dir.iterdir():
        if not flowcell_dir.is_dir():
            continue
        flowcell_name: str = flowcell_dir.name
        LOG.info("Check demuxed flowcell %s", flowcell_name)
        flowcell: Flowcell = Flowcell(flowcell_path=demultiplex_api.run_dir / flowcell_name)
        if not demultiplex_api.is_demultiplexing_completed(flowcell=flowcell):
            LOG.warning("Demultiplex is not ready for %s", flowcell_name)
            continue
        demux_results: DemuxResults = DemuxResults(
            demux_dir=demultiplex_api.out_dir / flowcell_name, flowcell=flowcell
        )
        demux_post_processing_api.set_dry_run(dry_run=dry_run)
        demux_post_processing_api.rename_files(demux_results=demux_results)
        demux_post_processing_api.add_to_cgstats(demux_results=demux_results)
        demux_post_processing_api.create_cgstats_reports(demux_results=demux_results)


@finish_group.command(name="flowcell")
@click.argument(
    "flowcell-name",
)
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def finish_flowcell(context: CGConfig, flowcell_name: str, dry_run: bool):
    """Command to finish up a flowcell after demultiplexing

    flowcell-name is full flowcell name, e.g. '201203_A00689_0200_AHVKJCDRXX'
    """
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    stats_api: StatsAPI = context.cg_stats_api
    demux_post_processing_api = DemuxPostProcessingAPI(stats_api=stats_api)
    flowcell: Flowcell = Flowcell(flowcell_path=demultiplex_api.run_dir / flowcell_name)
    demux_results: DemuxResults = DemuxResults(
        demux_dir=demultiplex_api.out_dir / flowcell_name, flowcell=flowcell
    )

    if not demultiplex_api.is_demultiplexing_completed(flowcell=flowcell):
        LOG.warning("Demultiplex is not ready!")
        raise click.Abort
    demux_post_processing_api.set_dry_run(dry_run=dry_run)
    demux_post_processing_api.rename_files(demux_results=demux_results)
    demux_post_processing_api.add_to_cgstats(demux_results=demux_results)
    demux_post_processing_api.create_cgstats_reports(demux_results=demux_results)
