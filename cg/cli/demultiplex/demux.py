import logging
from glob import glob
from pathlib import Path

import rich_click as click
from pydantic import ValidationError

from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.api import IlluminaSampleSheetService
from cg.apps.tb import TrailblazerAPI
from cg.cli.demultiplex.copy_novaseqx_demultiplex_data import (
    hardlink_flow_cell_analysis_data,
    is_ready_for_post_processing,
    mark_as_demultiplexed,
    mark_flow_cell_as_queued_for_post_processing,
    is_manifest_file_required,
    create_manifest_file,
    is_syncing_complete,
    is_flow_cell_sync_confirmed,
)
from cg.constants.cli_options import DRY_RUN
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import CgError, FlowCellError, SampleSheetContentError
from cg.models.cg_config import CGConfig
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData

LOG = logging.getLogger(__name__)


@click.command(name="all")
@click.option("--sequencing-runs-directory", type=click.Path(exists=True, file_okay=False))
@DRY_RUN
@click.pass_obj
def demultiplex_all(context: CGConfig, sequencing_runs_directory: click.Path, dry_run: bool):
    """Demultiplex all sequencing runs that are ready under the sequencing runs directory."""
    LOG.info("Running cg demultiplex all ...")
    sample_sheet_api: IlluminaSampleSheetService = context.sample_sheet_api
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    demultiplex_api.set_dry_run(dry_run=dry_run)
    if sequencing_runs_directory:
        sequencing_runs_directory: Path = Path(str(sequencing_runs_directory))
    else:
        sequencing_runs_directory: Path = Path(demultiplex_api.sequencing_runs_dir)

    LOG.info(f"Search for sequencing run ready to demultiplex in {sequencing_runs_directory}")
    for sub_dir in sequencing_runs_directory.iterdir():
        if not sub_dir.is_dir():
            continue
        LOG.info(f"Found directory {sub_dir}")
        try:
            sequencing_run = IlluminaRunDirectoryData(sequencing_run_path=sub_dir)
        except FlowCellError:
            continue

        if not demultiplex_api.is_demultiplexing_possible(sequencing_run=sequencing_run):
            LOG.warning(f"Can not start demultiplexing for sequencing run {sequencing_run.id}!")
            continue

        try:
            sample_sheet_api.validate_sample_sheet(sequencing_run.sample_sheet_path)
        except (CgError, ValidationError):
            LOG.warning(
                "Malformed sample sheet. Run "
                f"cg demultiplex samplesheet validate {sequencing_run.sample_sheet_path}"
            )
            continue

        if not dry_run:
            demultiplex_api.prepare_output_directory(sequencing_run)
            slurm_job_id: int = demultiplex_api.start_demultiplexing(sequencing_run=sequencing_run)
            tb_api: TrailblazerAPI = context.trailblazer_api
            demultiplex_api.add_to_trailblazer(
                tb_api=tb_api, slurm_job_id=slurm_job_id, sequencing_run=sequencing_run
            )


@click.command(name="sequencing-run")
@click.argument("sequencing-run-name")
@DRY_RUN
@click.pass_obj
def demultiplex_sequencing_run(
    context: CGConfig,
    dry_run: bool,
    sequencing_run_name: str,
):
    """Demultiplex an Illumina sequencing run using BCLConvert.


    sequencing run name is the sequencing run directory name, e.g. '230912_A00187_1009_AHK33MDRX3'
    """

    LOG.info(f"Starting demultiplexing of sequencing run {sequencing_run_name}")
    sample_sheet_api: IlluminaSampleSheetService = context.sample_sheet_api
    demultiplex_api: DemultiplexingAPI = context.demultiplex_api
    sequencing_run_dir: Path = Path(
        context.demultiplex_api.sequencing_runs_dir, sequencing_run_name
    )
    demultiplex_api.set_dry_run(dry_run=dry_run)
    LOG.info(f"setting flow cell id to {sequencing_run_name}")
    LOG.info(f"setting demultiplexed runs dir to {demultiplex_api.demultiplexed_runs_dir}")

    try:
        sequencing_run = IlluminaRunDirectoryData(sequencing_run_dir)
    except FlowCellError as error:
        raise click.Abort from error

    if not demultiplex_api.is_demultiplexing_possible(sequencing_run=sequencing_run):
        LOG.warning("Can not start demultiplexing!")
        return

    try:
        sample_sheet_api.validate_sample_sheet(sequencing_run.sample_sheet_path)
    except SampleSheetContentError:
        LOG.warning("Starting demultiplexing a with a manually modified sample sheet")
    except (CgError, ValidationError) as error:
        LOG.warning(
            "Malformed sample sheet. "
            f"Run cg demultiplex samplesheet validate {sequencing_run.sample_sheet_path}"
        )
        raise click.Abort from error

    if dry_run:
        LOG.info(f"Would have started demultiplexing {sequencing_run_name}")
        return
    demultiplex_api.prepare_output_directory(sequencing_run)
    slurm_job_id: int = demultiplex_api.start_demultiplexing(sequencing_run=sequencing_run)
    tb_api: TrailblazerAPI = context.trailblazer_api
    demultiplex_api.add_to_trailblazer(
        tb_api=tb_api, slurm_job_id=slurm_job_id, sequencing_run=sequencing_run
    )


@click.command(name="copy-completed-sequencing-runs")
@click.pass_obj
def copy_novaseqx_sequencing_runs(context: CGConfig):
    """Copy NovaSeq X sequencing runs ready for post-processing to demultiplexed runs."""
    sequencing_runs_dir: Path = Path(context.run_instruments.illumina.sequencing_runs_dir)
    demultiplexed_runs_dir: Path = Path(context.run_instruments.illumina.demultiplexed_runs_dir)

    for sequencing_run_dir in sequencing_runs_dir.iterdir():
        if is_ready_for_post_processing(
            flow_cell_dir=sequencing_run_dir, demultiplexed_runs_dir=demultiplexed_runs_dir
        ):
            LOG.info(f"Copying {sequencing_run_dir.name} to {demultiplexed_runs_dir}")
            hardlink_flow_cell_analysis_data(
                flow_cell_dir=sequencing_run_dir, demultiplexed_runs_dir=demultiplexed_runs_dir
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


@click.command(name="confirm-sequencing-run-sync")
@click.option(
    "--source-directory",
    required=True,
    help="The path from where the syncing is done.",
)
@click.pass_obj
def confirm_sequencing_run_sync(context: CGConfig, source_directory: str):
    """Checks if all relevant files for the demultiplexing have been synced.
    If so it creates a CopyComplete.txt file to show that that is the case."""
    target_sequencing_runs_directory = Path(context.run_instruments.illumina.sequencing_runs_dir)
    for source_sequencing_run in Path(source_directory).iterdir():
        target_sequencig_run = Path(target_sequencing_runs_directory, source_sequencing_run.name)
        if is_flow_cell_sync_confirmed(target_sequencig_run):
            LOG.debug(f"Flow cell {source_sequencing_run} has already been confirmed, skipping.")
            continue
        if is_syncing_complete(
            source_directory=source_sequencing_run,
            target_directory=Path(target_sequencing_runs_directory, source_sequencing_run.name),
        ):
            Path(
                target_sequencing_runs_directory,
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
    """Creates a file manifest for each sequencing run in the source directory."""
    for source_sequencing_run in glob(f"{source_directory}/*"):
        if is_manifest_file_required(Path(source_sequencing_run)):
            create_manifest_file(Path(source_sequencing_run))
