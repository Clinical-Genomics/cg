import logging
from pathlib import Path

import click

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER
from cg.exc import FlowcellError
from cg.meta.demultiplex.wipe_demultiplex_api import WipeDemuxAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flowcell import Flowcell

LOG = logging.getLogger(__name__)


@click.command(name="all")
@OPTION_BCL_CONVERTER
@click.option("--flowcells-directory", type=click.Path(exists=True, file_okay=False))
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def demultiplex_all(
    context: CGConfig, bcl_converter: str, flowcells_directory: click.Path, dry_run: bool
):
    """Demultiplex all flowcells that are ready under the flowcells_directory"""
    LOG.info("Running cg demultiplex all, using %s.", bcl_converter)
    if flowcells_directory:
        flowcells_directory: Path = Path(str(flowcells_directory))
    else:
        flowcells_directory: Path = Path(context.demultiplex.run_dir)
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    tb_api: TrailblazerAPI = context.trailblazer_api
    LOG.info("Search for flowcells ready to demultiplex in %s", flowcells_directory)
    for sub_dir in flowcells_directory.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info("Found directory %s", sub_dir)
        try:
            flowcell_obj = Flowcell(flowcell_path=sub_dir, bcl_converter=bcl_converter)
        except FlowcellError:
            continue

        if not demultiplex_api.is_demultiplexing_possible(flowcell=flowcell_obj) and not dry_run:
            continue

        if not flowcell_obj.validate_sample_sheet():
            LOG.warning(
                "Malformed sample sheet. Run cg demultiplex samplesheet validate %s",
                flowcell_obj.sample_sheet_path,
            )
            if not dry_run:
                continue

        wipe_demux_api: WipeDemuxAPI = WipeDemuxAPI(
            config=context,
            demultiplexing_dir=Path(demultiplex_api.out_dir),
            dry_run=dry_run,
            run_name=sub_dir,
        )

        wipe_demux_api.wipe_flow_cell(
            skip_cg_stats=False,
            skip_demultiplexing_dir=False,
            skip_run_dir=True,
            skip_housekeeper=False,
            skip_init_files=True,
            skip_status_db=True,
        )

        slurm_job_id: int = demultiplex_api.start_demultiplexing(flowcell=flowcell_obj)
        demultiplex_api.add_to_trailblazer(
            tb_api=tb_api, slurm_job_id=slurm_job_id, flowcell=flowcell_obj
        )


@click.command(name="flowcell")
@click.argument("flowcell-id")
@OPTION_BCL_CONVERTER
@click.option("--dry-run", is_flag=True)
@click.pass_obj
def demultiplex_flowcell(
    context: CGConfig,
    dry_run: bool,
    flowcell_id: str,
    bcl_converter: str,
):
    """Demultiplex a flowcell on slurm using CG

    flowcell-id is the flowcell run directory name, e.g. '201203_A00689_0200_AHVKJCDRXX'
    """

    LOG.info("Running cg demultiplex flowcell, using %s.", bcl_converter)
    flowcell_directory: Path = Path(context.demultiplex.run_dir) / flowcell_id

    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    LOG.info(f"SETTING FLOWCELL ID TO {flowcell_id}")
    LOG.info(f"SETTING OUT DIR TO {demultiplex_api.out_dir}")

    try:
        flowcell_obj = Flowcell(flowcell_path=flowcell_directory, bcl_converter=bcl_converter)
    except FlowcellError as e:
        raise click.Abort from e

    wipe_demux_api: WipeDemuxAPI = WipeDemuxAPI(
        config=context,
        demultiplexing_dir=Path(demultiplex_api.out_dir),
        dry_run=dry_run,
        run_name=flowcell_directory.name,
    )

    wipe_demux_api.wipe_flow_cell(
        skip_cg_stats=False,
        skip_demultiplexing_dir=False,
        skip_run_dir=True,
        skip_housekeeper=False,
        skip_init_files=False,
        skip_status_db=True,
    )

    if not demultiplex_api.is_demultiplexing_possible(flowcell=flowcell_obj) and not dry_run:
        LOG.warning("Can not start demultiplexing!")
        return

    if not flowcell_obj.validate_sample_sheet():
        LOG.warning(
            "Malformed sample sheet. Run cg demultiplex samplesheet validate %s",
            flowcell_obj.sample_sheet_path,
        )
        if not dry_run:
            raise click.Abort

    slurm_job_id: int = demultiplex_api.start_demultiplexing(flowcell=flowcell_obj)
    tb_api: TrailblazerAPI = context.trailblazer_api
    demultiplex_api.add_to_trailblazer(
        tb_api=tb_api, slurm_job_id=slurm_job_id, flowcell=flowcell_obj
    )


@click.command(name="wipe-flow-cell")
@click.option("--dry-run", is_flag=True)
@click.option("--skip-cg-stats", is_flag=True, help="Skip removal in cg-stats")
@click.option("--skip-demultiplexing-dir", is_flag=True, help="Skip removal on server file system")
@click.option("--skip-run-dir", is_flag=True, help="Skip removal of run file system")
@click.option("--skip-housekeeper", is_flag=True, help="Skip removal in housekeeper")
@click.option("--skip-status-db", is_flag=True, help="Skip removal in status-db")
@click.option("--skip-init-files", is_flag=True, help="Skip removal of init-files")
@click.argument("--demultiplexing-dir")
@click.argument("--run-name")
def wipe_flow_cell(
    context: CGConfig,
    dry_run: bool,
    demultiplexing_dir: str,
    run_name: str,
    skip_cg_stats: bool,
    skip_demultiplexing_dir: bool,
    skip_housekeeper: bool,
    skip_init_files: bool,
    skip_run_dir: bool,
    skip_status_db: bool,
):
    """Prepare a flowcell before demultiplexing, using the WipeDemuxAPI

    Args:
        Run name is the flowcell run directory name, e.g. '201203_A00689_0200_AHVKJCDRXX'
        Demultiplexing-dir is the base of demultiplexing, e.g. '/home/proj/{ENVIRONMENT}/demultiplexed-runs/'
    """

    demux_path: Path = Path(demultiplexing_dir)

    wipe_demux_api: WipeDemuxAPI = WipeDemuxAPI(
        config=context, demultiplexing_dir=demux_path, run_name=run_name
    )
    wipe_demux_api.set_dry_run(dry_run=dry_run)
    wipe_demux_api.wipe_flow_cell(
        skip_cg_stats=skip_cg_stats,
        skip_demultiplexing_dir=skip_demultiplexing_dir,
        skip_housekeeper=skip_housekeeper,
        skip_init_files=skip_init_files,
        skip_run_dir=skip_run_dir,
        skip_status_db=skip_status_db,
    )
