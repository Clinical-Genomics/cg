import logging
import os
import shutil
from pathlib import Path

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.io.csv import read_csv, write_csv

LOG = logging.getLogger(__name__)

NANOPORE_SEQUENCING_SUMMARY_PATTERN: str = r"final_summary_*.txt"


def is_demultiplexing_copied(analysis_directory: Path) -> bool:
    """Determine whether the demultiplexing has been copied for the latest analysis for a Novaseqx flow cell."""
    return Path(analysis_directory, DemultiplexingDirsAndFiles.COPY_COMPLETE).exists()


def is_flow_cell_demultiplexed(analysis_directory: Path) -> bool:
    """Determine whether the flow cell has been demultiplexed for the latest analysis for a Novaseqx flow cell."""
    return Path(
        analysis_directory,
        DemultiplexingDirsAndFiles.DATA,
        DemultiplexingDirsAndFiles.ANALYSIS_COMPLETED,
    ).exists()


def is_flow_cell_in_demultiplexed_runs(flow_cell_name: str, demultiplexed_runs: Path) -> bool:
    """Determine whether the flow cell is in the demultiplexed runs directory."""
    return Path(demultiplexed_runs, flow_cell_name).exists()


def get_latest_analysis_path(flow_cell_dir: Path) -> Path | None:
    """
    Get the latest analysis directory for a Novaseqx flow cell.
    The latest analysis directory is the one with the highest integer name.
    """
    analysis_path: Path = Path(flow_cell_dir, DemultiplexingDirsAndFiles.ANALYSIS)
    if not analysis_path.exists():
        return None
    analysis_versions: list[Path] = get_sorted_analysis_versions(analysis_path)
    return analysis_versions[0] if analysis_versions else None


def get_sorted_analysis_versions(analysis_path: Path) -> list[Path]:
    """Get a sorted list of analysis version paths for a Novaseqx flow cell."""

    def sort_by_name(version: Path) -> int:
        return int(version.name)

    analysis_versions_paths: list[Path] = [
        version_path for version_path in analysis_path.iterdir() if version_path.is_dir()
    ]
    return sorted(analysis_versions_paths, key=sort_by_name, reverse=True)


def is_queued_for_post_processing(flow_cell_dir: Path) -> bool:
    """Determine whether the flow cell is queued for post processing."""
    return Path(flow_cell_dir, DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING).exists()


def hardlink_flow_cell_analysis_data(flow_cell_dir: Path, demultiplexed_runs_dir: Path) -> None:
    """Create hardlinks to the latest version of the analysis data for a Novaseqx flow cell."""
    analysis_path: Path = get_latest_analysis_path(flow_cell_dir)
    analysis_data_path: Path = Path(analysis_path, DemultiplexingDirsAndFiles.DATA)
    demultiplexed_runs_dir_flow_cell_dir = Path(demultiplexed_runs_dir, flow_cell_dir.name)
    hardlink_tree(src=analysis_data_path, dst=demultiplexed_runs_dir_flow_cell_dir)


def mark_as_demultiplexed(flow_cell_dir: Path) -> None:
    """Create the demux_complete.txt file in the specified flow cell directory."""
    Path(flow_cell_dir, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()


def mark_flow_cell_as_queued_for_post_processing(flow_cell_dir: Path) -> None:
    """Create the queued_for_post_processing.txt file in the specified flow cell directory."""
    Path(flow_cell_dir, DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING).touch()


def hardlink_tree(src: Path, dst: Path) -> None:
    """Create hardlinks to the specified source directory in the specified destination directory."""
    shutil.copytree(src=src, dst=dst, copy_function=os.link)


def is_ready_for_post_processing(flow_cell_dir: Path, demultiplexed_runs_dir: Path) -> bool:
    """
    Determine whether the flow cell is ready for post processing.
    The flow cell is ready for post processing if:
    - the demultiplexing has been copied
    - the flow cell has been demultiplexed
    - the flow cell is not in the demultiplexed runs directory
    - the flow cell is not queued for post processing
    """
    analysis_path: Path = get_latest_analysis_path(flow_cell_dir)

    if not analysis_path:
        LOG.debug(f"No analysis path found for flow cell {flow_cell_dir.name}.")
        return False

    flow_cell_is_ready: bool = True

    if not is_demultiplexing_copied(analysis_path):
        LOG.debug(f"Demultiplexing has not been copied for flow cell {flow_cell_dir.name}.")
        flow_cell_is_ready = False
    if not is_flow_cell_demultiplexed(analysis_path):
        LOG.debug(f"Flow cell {flow_cell_dir.name} has not been demultiplexed.")
        flow_cell_is_ready = False

    if is_flow_cell_in_demultiplexed_runs(
        flow_cell_name=flow_cell_dir.name, demultiplexed_runs=demultiplexed_runs_dir
    ):
        LOG.debug(f"Flow cell {flow_cell_dir.name} is already in the demultiplexed runs directory.")
        flow_cell_is_ready = False

    if is_queued_for_post_processing(flow_cell_dir):
        LOG.debug(f"Flow cell {flow_cell_dir.name} is already queued for post processing.")
        flow_cell_is_ready = False

    return flow_cell_is_ready


def get_existing_manifest_file(source_directory: Path) -> Path | None:
    """Returns the first existing manifest file in the source directory."""
    manifest_file_paths = [
        Path(source_directory, DemultiplexingDirsAndFiles.ILLUMINA_FILE_MANIFEST),
        Path(source_directory, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST),
    ]
    for file_path in manifest_file_paths:
        if file_path.exists():
            return file_path


def are_all_files_synced(files_at_source: list[Path], target_directory: Path) -> bool:
    """Checks if all relevant files in the source are present in the target directory."""
    for file in files_at_source:
        target_file_path = Path(target_directory, file)
        if is_file_relevant_for_demultiplexing(file) and not target_file_path.exists():
            LOG.info(f"File: {file}, has not been transferred from source to {target_directory}")
            return False
    return True


def is_syncing_complete(source_directory: Path, target_directory: Path) -> bool:
    """Returns whether all relevant files for demultiplexing have been synced from the source to the target."""
    existing_manifest_file: Path | None = get_existing_manifest_file(source_directory)

    if not existing_manifest_file:
        LOG.debug(f"{source_directory} does not contain a manifest file. Skipping.")
        return False

    files_at_source: list[Path] = parse_manifest_file(existing_manifest_file)
    return are_all_files_synced(files_at_source=files_at_source, target_directory=target_directory)


def is_manifest_file_required(flow_cell_dir: Path) -> bool:
    """Returns whether a flow cell directory needs a manifest file."""
    illumina_manifest_file = Path(flow_cell_dir, DemultiplexingDirsAndFiles.ILLUMINA_FILE_MANIFEST)
    custom_manifest_file = Path(flow_cell_dir, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)
    copy_complete_file = Path(flow_cell_dir, DemultiplexingDirsAndFiles.COPY_COMPLETE)
    sequencing_finished: bool = copy_complete_file.exists() or is_nanopore_sequencing_complete(
        flow_cell_dir
    )
    return (
        not any((illumina_manifest_file.exists(), custom_manifest_file.exists()))
        and sequencing_finished
    )


def create_manifest_file(flow_cell_dir_name: Path) -> Path:
    """Creates a tab separated file containing the paths of all files in the given
    directory and any subdirectories."""
    files_in_directory: list[list[str]] = []
    for subdir, _, files in os.walk(flow_cell_dir_name):
        subdir = Path(subdir).relative_to(flow_cell_dir_name)
        files_in_directory.extend([Path(subdir, file).as_posix()] for file in files)
    LOG.info(
        f"Writing manifest file to {Path(flow_cell_dir_name, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)}"
    )
    output_path = Path(flow_cell_dir_name, DemultiplexingDirsAndFiles.CG_FILE_MANIFEST)
    write_csv(
        content=files_in_directory,
        file_path=output_path,
        delimiter="\t",
    )
    return output_path


def is_flow_cell_sync_confirmed(target_flow_cell_dir: Path) -> bool:
    return Path(target_flow_cell_dir, DemultiplexingDirsAndFiles.COPY_COMPLETE).exists()


def get_nanopore_summary_file(flow_cell_directory: Path) -> bool | None:
    """Returns the summary file for a Nanopore run if found."""
    try:
        file = Path(next(flow_cell_directory.glob(NANOPORE_SEQUENCING_SUMMARY_PATTERN)))
    except StopIteration:
        file = None
    return file


def is_nanopore_sequencing_complete(flow_cell_directory: Path) -> bool:
    """Returns whether the sequencing is complete for a Nanopore run."""
    return bool(get_nanopore_summary_file(flow_cell_directory))


def parse_manifest_file(manifest_file: Path) -> list[Path]:
    """Returns a list with the first entry of each row of the given TSV file."""
    LOG.debug(f"Parsing manifest file: {manifest_file}")
    files: list[list[str]] = read_csv(file_path=manifest_file, delimiter="\t")
    return [Path(file[0]) for file in files]


def is_file_relevant_for_demultiplexing(file: Path) -> bool:
    """Returns whether a file is relevant for demultiplexing."""
    relevant_directories = [DemultiplexingDirsAndFiles.INTER_OP, DemultiplexingDirsAndFiles.DATA]
    for relevant_directory in relevant_directories:
        if relevant_directory in file.parts:
            return True
    return False
