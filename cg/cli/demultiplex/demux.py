import logging
from pathlib import Path
from typing import List, Optional

import click
import os
import shutil

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER, DemultiplexingDirsAndFiles
from cg.exc import FlowCellError
from cg.meta.demultiplex.delete_demultiplex_api import DeleteDemuxAPI
from cg.models.cg_config import CGConfig
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


LOG = logging.getLogger(__name__)

DRY_RUN = click.option("--dry-run", is_flag=True)


@click.command(name="all")
@click.option("--flow-cells-directory", type=click.Path(exists=True, file_okay=False))
@DRY_RUN
@click.pass_obj
def demultiplex_all(context: CGConfig, flow_cells_directory: click.Path, dry_run: bool):
    """Demultiplex all flow cells that are ready under the flow cells directory."""
    LOG.info("Running cg demultiplex all ...")
    if flow_cells_directory:
        flow_cells_directory: Path = Path(str(flow_cells_directory))
    else:
        flow_cells_directory: Path = Path(context.demultiplex.run_dir)
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    tb_api: TrailblazerAPI = context.trailblazer_api
    LOG.info(f"Search for flow cells ready to demultiplex in {flow_cells_directory}")
    for sub_dir in flow_cells_directory.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info(f"Found directory {sub_dir}")
        try:
            flow_cell = FlowCellDirectoryData(flow_cell_path=sub_dir)
            LOG.info(f"Using {flow_cell.bcl_converter} for demultiplexing.")
        except FlowCellError:
            continue

        if not demultiplex_api.is_demultiplexing_possible(flow_cell=flow_cell) and not dry_run:
            continue

        if not flow_cell.validate_sample_sheet():
            LOG.warning(
                f"Malformed sample sheet. Run cg demultiplex samplesheet validate {flow_cell.sample_sheet_path}",
            )
            continue

        slurm_job_id: int = demultiplex_api.start_demultiplexing(flow_cell=flow_cell)
        demultiplex_api.add_to_trailblazer(
            tb_api=tb_api, slurm_job_id=slurm_job_id, flow_cell=flow_cell
        )


@click.command(name="flow-cell")
@click.argument("flow-cell-name")
@DRY_RUN
@OPTION_BCL_CONVERTER
@click.pass_obj
def demultiplex_flow_cell(
    context: CGConfig,
    dry_run: bool,
    flow_cell_name: str,
    bcl_converter: str,
):
    """Demultiplex a flow cell.

    flow cell name is the flow cell run directory name, e.g. '201203_A00689_0200_AHVKJCDRXX'
    """

    LOG.info(f"Running cg demultiplex flow cell, using {bcl_converter}")
    flow_cell: Path = Path(context.demultiplex.run_dir, flow_cell_name)

    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    LOG.info(f"setting flow cell id to {flow_cell_name}")
    LOG.info(f"setting out dir to {demultiplex_api.out_dir}")

    try:
        flow_cell = FlowCellDirectoryData(flow_cell_path=flow_cell, bcl_converter=bcl_converter)
    except FlowCellError as error:
        raise click.Abort from error

    if not demultiplex_api.is_demultiplexing_possible(flow_cell=flow_cell) and not dry_run:
        LOG.warning("Can not start demultiplexing!")
        return

    if not flow_cell.validate_sample_sheet():
        LOG.warning(
            f"Malformed sample sheet. Run cg demultiplex samplesheet validate {flow_cell.sample_sheet_path}"
        )
        raise click.Abort

    slurm_job_id: int = demultiplex_api.start_demultiplexing(flow_cell=flow_cell)
    tb_api: TrailblazerAPI = context.trailblazer_api
    demultiplex_api.add_to_trailblazer(
        tb_api=tb_api, slurm_job_id=slurm_job_id, flow_cell=flow_cell
    )


@click.command(name="delete-flow-cell")
@click.option(
    "-f",
    "--flow-cell-name",
    required=True,
    help="The name of the flow cell you want to delete, e.g. HVKJCDRXX",
)
@click.option(
    "--demultiplexing-dir", is_flag=True, help="Delete flow cell demultiplexed dir on file system"
)
@click.option("--cg-stats", is_flag=True, help="Delete flow cell in cg-stats")
@click.option("--housekeeper", is_flag=True, help="Delete flow cell in housekeeper")
@click.option("--init-files", is_flag=True, help="Delete flow cell init-files")
@click.option("--run-dir", is_flag=True, help="Delete flow cell run on file system")
@click.option(
    "--sample-lane-sequencing-metrics",
    is_flag=True,
    help="Delete flow cell in sample lane sequencing metrics",
)
@click.option(
    "--status-db",
    is_flag=True,
    help="Delete flow cell in status-db, if passed all other entries are also deleted",
)
@click.option("--yes", is_flag=True, help="Pass yes to click confirm")
@DRY_RUN
@click.pass_obj
def delete_flow_cell(
    context: CGConfig,
    dry_run: bool,
    demultiplexing_dir: bool,
    cg_stats: bool,
    housekeeper: bool,
    init_files: bool,
    run_dir: bool,
    sample_lane_sequencing_metrics: bool,
    status_db: bool,
    yes: bool,
    flow_cell_name: str,
):
    """Delete a flow cell. If --status-db is passed then all other options will be treated as True."""

    delete_demux_api: DeleteDemuxAPI = DeleteDemuxAPI(
        config=context, dry_run=dry_run, flow_cell_name=flow_cell_name
    )

    if yes or click.confirm(
        f"Are you sure you want to delete the flow cell from the following databases:\n"
        f"cg-stats={True if status_db else cg_stats}\nDemultiplexing-dir={True if status_db else demultiplexing_dir}\n"
        f"Housekeeper={True if status_db else housekeeper}\nInit_files={True if status_db else init_files}\n"
        f"Run-dir={True if status_db else run_dir}\nStatusdb={status_db}\n"
        f"\nSample-lane-sequencing-metrics={True if sample_lane_sequencing_metrics else sample_lane_sequencing_metrics}"
    ):
        delete_demux_api.delete_flow_cell(
            cg_stats=cg_stats,
            demultiplexing_dir=demultiplexing_dir,
            housekeeper=housekeeper,
            init_files=init_files,
            sample_lane_sequencing_metrics=sample_lane_sequencing_metrics,
            run_dir=run_dir,
            status_db=status_db,
        )


@click.command(name="copy-novaseqx")
def copy_novaseqx_flow_cells(context: CGConfig):
    """Copy novaseqx flow cells ready for post processing to demultiplexed runs."""
    flow_cells: Path = context.demultiplex.out_dir
    demultiplexed_runs: Path = context.demultiplex.run_dir

    for flow_cell in flow_cells.iterdir():
        if is_ready_for_post_processing(flow_cell, demultiplexed_runs):
            copy_flow_cell_analysis_data(flow_cell, demultiplexed_runs)
            demultiplexed_flow_cell = Path(demultiplexed_runs, flow_cell.name)
            mark_flow_cell_as_demultiplexed(demultiplexed_flow_cell)
            mark_flow_cell_as_queued_for_post_processing(flow_cell)


def is_ready_for_post_processing(flow_cell: Path, demultiplexed_runs: Path) -> bool:
    analysis_directory = get_latest_analysis_directory(flow_cell)

    if not analysis_directory:
        return False

    copy_completed = is_copied(analysis_directory)
    analysis_completed = is_analyzed(analysis_directory)
    in_demultiplexed_runs = is_in_demultiplexed_runs(flow_cell.name, demultiplexed_runs)
    post_processed = is_queued_for_post_processing(flow_cell)

    return (
        copy_completed and analysis_completed and not in_demultiplexed_runs and not post_processed
    )


def is_in_demultiplexed_runs(flow_cell_name: str, demultiplexed_runs: Path) -> bool:
    return Path(demultiplexed_runs, flow_cell_name).exists()


def get_latest_analysis_directory(flow_cell: Path) -> Optional[Path]:
    analysis_path = Path(flow_cell, DemultiplexingDirsAndFiles.ANALYSIS)

    if not analysis_path.exists():
        return None
    analysis_versions = get_sorted_analysis_versions(analysis_path)
    return analysis_versions[0] if analysis_versions else None


def get_sorted_analysis_versions(analysis_path: Path) -> List[Path]:
    return sorted(
        (d for d in analysis_path.iterdir() if d.is_dir()), key=lambda x: int(x.name), reverse=True
    )


def is_copied(analysis_directory: Path):
    return Path(analysis_directory, DemultiplexingDirsAndFiles.COPY_COMPLETE).exists()


def is_analyzed(analysis_directory: Path):
    return Path(
        analysis_directory,
        DemultiplexingDirsAndFiles.DATA,
        DemultiplexingDirsAndFiles.ANALYSIS_COMPLETED,
    ).exists()


def is_queued_for_post_processing(flow_cell: Path) -> bool:
    return Path(flow_cell, DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING).exists()


def copy_flow_cell_analysis_data(flow_cell: Path, destination: Path) -> None:
    analysis = get_latest_analysis_directory(flow_cell)
    analysis_data = Path(analysis, DemultiplexingDirsAndFiles.DATA)

    hardlink_tree(src=analysis_data, dst=destination)


def mark_flow_cell_as_demultiplexed(flow_cell: Path) -> None:
    Path(flow_cell, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()


def mark_flow_cell_as_queued_for_post_processing(flow_cell: Path) -> None:
    Path(flow_cell, DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING).touch()


def hardlink_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, copy_function=os.link)
