import logging
import os
import shutil
from pathlib import Path

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles

LOG = logging.getLogger(__name__)


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
