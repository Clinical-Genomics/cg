import logging
from pathlib import Path

import click

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.tb import TrailblazerAPI
from cg.cli.demultiplex.copy_novaseqx_demultiplex_data import (
    hardlink_flow_cell_analysis_data,
    is_ready_for_post_processing,
    mark_as_demultiplexed,
    mark_flow_cell_as_queued_for_post_processing,
)
from cg.constants.demultiplexing import OPTION_BCL_CONVERTER, DemultiplexingDirsAndFiles
from cg.exc import FlowCellError
from cg.meta.demultiplex.delete_demultiplex_api import DeleteDemuxAPI
from cg.meta.demultiplex.utils import (
    create_manifest_file,
    is_flow_cell_sync_confirmed,
    is_manifest_file_required,
    is_syncing_complete,
)
from cg.models.cg_config import CGConfig
from cg.models.flow_cell.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)

DRY_RUN = click.option("--dry-run", is_flag=True)


@click.command(name="all")
@click.option("--flow-cells-directory", type=click.Path(exists=True, file_okay=False))
@DRY_RUN
@click.pass_obj
def demultiplex_all(context: CGConfig, flow_cells_directory: click.Path, dry_run: bool):
    """Demultiplex all flow cells that are ready under the flow cells directory."""
    LOG.info("Running cg demultiplex all ...")
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    if flow_cells_directory:
        flow_cells_directory: Path = Path(str(flow_cells_directory))
    else:
        flow_cells_directory: Path = Path(demultiplex_api.flow_cells_dir)

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

        if not demultiplex_api.is_demultiplexing_possible(flow_cell=flow_cell):
            LOG.warning(f"Can not start demultiplexing for flow cell {flow_cell.id}!")
            continue

        if not flow_cell.validate_sample_sheet():
            LOG.warning(
                f"Malformed sample sheet. Run cg demultiplex samplesheet validate {flow_cell.sample_sheet_path}",
            )
            continue

        if not dry_run:
            slurm_job_id: int = demultiplex_api.start_demultiplexing(flow_cell=flow_cell)
            tb_api: TrailblazerAPI = context.trailblazer_api
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

    flow cell name is the flow cell run directory name, e.g. '201203_D00483_0200_AHVKJCDRXX'
    """

    LOG.info(f"Running cg demultiplex flow cell, using {bcl_converter}")
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    flow_cell_directory: Path = Path(context.demultiplex_api.flow_cells_dir, flow_cell_name)
    demultiplex_api.set_dry_run(dry_run=dry_run)
    LOG.info(f"setting flow cell id to {flow_cell_name}")
    LOG.info(f"setting demultiplexed runs dir to {demultiplex_api.demultiplexed_runs_dir}")

    try:
        flow_cell = FlowCellDirectoryData(
            flow_cell_path=flow_cell_directory, bcl_converter=bcl_converter
        )
    except FlowCellError as error:
        raise click.Abort from error

    if not demultiplex_api.is_demultiplexing_possible(flow_cell=flow_cell):
        LOG.warning("Can not start demultiplexing!")
        return

    if not flow_cell.validate_sample_sheet():
        LOG.warning(
            f"Malformed sample sheet. Run cg demultiplex samplesheet validate {flow_cell.sample_sheet_path}"
        )
        raise click.Abort

    if not dry_run:
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
        f"Housekeeper={True if status_db else housekeeper}\nInit_files={True if status_db else init_files}\n"
        f"Run-dir={True if status_db else run_dir}\nStatusdb={status_db}\n"
        f"\nSample-lane-sequencing-metrics={True if sample_lane_sequencing_metrics else sample_lane_sequencing_metrics}"
    ):
        delete_demux_api.delete_flow_cell(
            demultiplexing_dir=demultiplexing_dir,
            housekeeper=housekeeper,
            init_files=init_files,
            sample_lane_sequencing_metrics=sample_lane_sequencing_metrics,
            run_dir=run_dir,
            status_db=status_db,
        )


@click.command(name="copy-completed-flow-cell")
@click.pass_obj
def copy_novaseqx_flow_cells(context: CGConfig):
    """Copy Novaseqx flow cells ready for post processing to demultiplexed runs."""
    flow_cells_dir: Path = Path(context.flow_cells_dir)
    demultiplexed_runs_dir: Path = Path(context.demultiplexed_flow_cells_dir)

    for flow_cell_dir in flow_cells_dir.iterdir():
        if is_ready_for_post_processing(
            flow_cell_dir=flow_cell_dir, demultiplexed_runs_dir=demultiplexed_runs_dir
        ):
            LOG.info(f"Copying {flow_cell_dir.name} to {demultiplexed_runs_dir}")
            hardlink_flow_cell_analysis_data(
                flow_cell_dir=flow_cell_dir, demultiplexed_runs_dir=demultiplexed_runs_dir
            )
            demultiplexed_runs_flow_cell_dir: Path = Path(
                demultiplexed_runs_dir, flow_cell_dir.name
            )
            mark_as_demultiplexed(demultiplexed_runs_flow_cell_dir)
            mark_flow_cell_as_queued_for_post_processing(flow_cell_dir)
        else:
            LOG.info(f"Flow cell {flow_cell_dir.name} is not ready for post processing, skipping.")


@click.command(name="confirm-flow-cell-sync")
@click.option(
    "--source-directory",
    required=True,
    help="The path from where the syncing is done.",
)
@click.pass_obj
def confirm_flow_cell_sync(context: CGConfig, source_directory: str):
    """Checks if all relevant files for the demultiplexing have been synced.
    If so it creates a CopyComplete.txt file to show that that is the case."""
    target_flow_cells_directory = Path(context.flow_cells_dir)
    for source_flow_cell in Path(source_directory).iterdir():
        target_flow_cell = Path(target_flow_cells_directory, source_flow_cell.name)
        if is_flow_cell_sync_confirmed(target_flow_cell):
            LOG.debug(f"Flow cell {source_flow_cell} has already been confirmed, skipping.")
            continue
        if is_syncing_complete(
            source_directory=source_flow_cell,
            target_directory=Path(target_flow_cells_directory, source_flow_cell.name),
        ):
            Path(
                target_flow_cells_directory,
                source_flow_cell.name,
                DemultiplexingDirsAndFiles.COPY_COMPLETE,
            ).touch()


@click.command(name="create-manifest-files")
@click.option(
    "--source-directory",
    required=True,
    help="The path from where the syncing is done.",
)
def create_manifest_files(source_directory: str):
    for source_flow_cell in Path(source_directory).iterdir():
        if is_manifest_file_required(source_flow_cell):
            create_manifest_file(source_flow_cell)
