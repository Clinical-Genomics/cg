import logging
from glob import glob
from pathlib import Path

import click
from pydantic import ValidationError

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.api import SampleSheetAPI
from cg.apps.tb import TrailblazerAPI
from cg.cli.demultiplex.copy_novaseqx_demultiplex_data import (
    hardlink_sequencing_run_analysis_data,
    is_ready_for_post_processing,
    mark_as_demultiplexed,
    mark_flow_cell_as_queued_for_post_processing,
)
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.constants import DRY_RUN
from cg.exc import FlowCellError, SampleSheetError
from cg.meta.demultiplex.utils import (
    create_manifest_file,
    is_flow_cell_sync_confirmed,
    is_manifest_file_required,
    is_syncing_complete,
)
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory import (
    IlluminaRunDirectory,
)

LOG = logging.getLogger(__name__)


@click.command(name="all")
@click.option("--flow-cell-runs-directory", type=click.Path(exists=True, file_okay=False))
@DRY_RUN
@click.pass_obj
def demultiplex_all(context: CGConfig, flow_cell_runs_directory: click.Path, dry_run: bool):
    """Demultiplex all flow cells that are ready under the flow cells directory."""
    LOG.info("Running cg demultiplex all ...")
    sample_sheet_api: SampleSheetAPI = context.sample_sheet_api
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    if flow_cell_runs_directory:
        flow_cell_runs_directory: Path = Path(str(flow_cell_runs_directory))
    else:
        flow_cell_runs_directory: Path = Path(demultiplex_api.runs_dir)

    LOG.info(f"Search for flow cells ready to demultiplex in {flow_cell_runs_directory}")
    for sub_dir in flow_cell_runs_directory.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info(f"Found directory {sub_dir}")
        try:
            run_dir = IlluminaRunDirectory(sequencing_run_path=sub_dir)
        except FlowCellError:
            continue

        if not demultiplex_api.is_demultiplexing_possible(run_dir=run_dir):
            LOG.warning(f"Can not start demultiplexing for flow cell {run_dir.id}!")
            continue

        try:
            sample_sheet_api.validate_sample_sheet(run_dir.sample_sheet_path)
        except (SampleSheetError, ValidationError):
            LOG.warning(
                f"Malformed sample sheet. Run cg demultiplex samplesheet validate {run_dir.sample_sheet_path}"
            )
            continue

        if not dry_run:
            demultiplex_api.prepare_output_directory(run_dir)
            slurm_job_id: int = demultiplex_api.start_demultiplexing(run_dir=run_dir)
            tb_api: TrailblazerAPI = context.trailblazer_api
            demultiplex_api.add_to_trailblazer(
                tb_api=tb_api, slurm_job_id=slurm_job_id, run_dir=run_dir
            )


@click.command(name="flow-cell")
@click.argument("flow-cell-name")
@DRY_RUN
@click.pass_obj
def demultiplex_flow_cell(
    context: CGConfig,
    dry_run: bool,
    flow_cell_name: str,
):
    """Demultiplex a flow cell using BCLConvert.

    flow cell name is the flow cell run directory name, e.g. '230912_A00187_1009_AHK33MDRX3'
    """

    LOG.info(f"Starting demultiplexing of flow cell {flow_cell_name}")
    sample_sheet_api: SampleSheetAPI = context.sample_sheet_api
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    sequencing_run_directory: Path = Path(context.demultiplex_api.runs_dir, flow_cell_name)
    demultiplex_api.set_dry_run(dry_run=dry_run)
    LOG.info(f"setting flow cell id to {flow_cell_name}")
    LOG.info(f"setting demultiplexed runs dir to {demultiplex_api.demultiplexed_runs_dir}")

    try:
        run_dir = IlluminaRunDirectory(sequencing_run_directory)
    except FlowCellError as error:
        raise click.Abort from error

    if not demultiplex_api.is_demultiplexing_possible(run_dir=run_dir):
        LOG.warning("Can not start demultiplexing!")
        return

    try:
        sample_sheet_api.validate_sample_sheet(run_dir.sample_sheet_path)
    except (SampleSheetError, ValidationError) as error:
        LOG.warning(
            f"Malformed sample sheet. Run cg demultiplex samplesheet validate {run_dir.sample_sheet_path}"
        )
        raise click.Abort from error

    if not dry_run:
        demultiplex_api.prepare_output_directory(run_dir)
        slurm_job_id: int = demultiplex_api.start_demultiplexing(run_dir=run_dir)
        tb_api: TrailblazerAPI = context.trailblazer_api
        demultiplex_api.add_to_trailblazer(
            tb_api=tb_api, slurm_job_id=slurm_job_id, run_dir=run_dir
        )


@click.command(name="copy-completed-flow-cell")
@click.pass_obj
def copy_novaseqx_flow_cells(context: CGConfig):
    """Copy NovaSeq X flow cells ready for post-processing to demultiplexed runs."""
    sequencing_runs_dir: Path = Path(context.illumina_flow_cells_directory)
    demultiplexed_runs_dir: Path = Path(context.illumina_demultiplexed_runs_directory)

    for sequencing_run_dir in sequencing_runs_dir.iterdir():
        if is_ready_for_post_processing(
            sequencing_run_dir=sequencing_run_dir, demultiplexed_runs_dir=demultiplexed_runs_dir
        ):
            LOG.info(f"Copying {sequencing_run_dir.name} to {demultiplexed_runs_dir}")
            hardlink_sequencing_run_analysis_data(
                sequencing_run_dir=sequencing_run_dir, demultiplexed_runs_dir=demultiplexed_runs_dir
            )
            demultiplexed_runs_flow_cell_dir: Path = Path(
                demultiplexed_runs_dir, sequencing_run_dir.name
            )
            mark_as_demultiplexed(demultiplexed_runs_flow_cell_dir)
            mark_flow_cell_as_queued_for_post_processing(sequencing_run_dir)
        else:
            LOG.info(
                f"Flow cell {sequencing_run_dir.name} is not ready for post processing, skipping."
            )


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
    target_sequencing_run_directory = Path(context.illumina_flow_cells_directory)
    for source_sequencing_run in Path(source_directory).iterdir():
        target_sequencing_run = Path(target_sequencing_run_directory, source_sequencing_run.name)
        if is_flow_cell_sync_confirmed(target_sequencing_run):
            LOG.debug(f"Flow cell {source_sequencing_run} has already been confirmed, skipping.")
            continue
        if is_syncing_complete(
            source_directory=source_sequencing_run,
            target_directory=Path(target_sequencing_run_directory, source_sequencing_run.name),
        ):
            Path(
                target_sequencing_run_directory,
                source_sequencing_run.name,
                DemultiplexingDirsAndFiles.COPY_COMPLETE,
            ).touch()


@click.command(name="create-manifest-files")
@click.option(
    "--source-directory",
    required=True,
    help="The path from where the syncing is done.",
)
def create_manifest_files(source_directory: str):
    """Creates a file manifest for each flow cell in the source directory."""
    for source_sequencing_run in glob(f"{source_directory}/*"):
        if is_manifest_file_required(Path(source_sequencing_run)):
            create_manifest_file(Path(source_sequencing_run))
