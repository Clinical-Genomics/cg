from pathlib import Path
import os
import shutil
from typing import List, Optional

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles


def is_copied(analysis_directory: Path) -> bool:
    return Path(analysis_directory, DemultiplexingDirsAndFiles.COPY_COMPLETE).exists()


def is_analyzed(analysis_directory: Path) -> bool:
    return Path(
        analysis_directory,
        DemultiplexingDirsAndFiles.DATA,
        DemultiplexingDirsAndFiles.ANALYSIS_COMPLETED,
    ).exists()


def is_in_demultiplexed_runs(flow_cell: Path, demultiplexed_runs: Path) -> bool:
    return Path(demultiplexed_runs, flow_cell.name).exists()


def get_latest_analysis_directory(flow_cell_dir: Path) -> Optional[Path]:
    analysis_path = Path(flow_cell_dir, DemultiplexingDirsAndFiles.ANALYSIS)

    if not analysis_path.exists():
        return None
    analysis_versions = get_sorted_analysis_versions(analysis_path)
    return analysis_versions[0] if analysis_versions else None


def get_sorted_analysis_versions(analysis_path: Path) -> List[Path]:
    def sort_by_name(version: Path) -> int:
        return int(version.name)

    analysis_versions = [version for version in analysis_path.iterdir() if version.is_dir()]
    sorted_versions = sorted(analysis_versions, key=sort_by_name, reverse=True)
    return sorted_versions


def is_queued_for_post_processing(flow_cell_dir: Path) -> bool:
    return Path(flow_cell_dir, DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING).exists()


def copy_flow_cell_analysis_data(flow_cell_dir: Path, destination: Path) -> None:
    analysis: Path = get_latest_analysis_directory(flow_cell_dir)
    analysis_data = Path(analysis, DemultiplexingDirsAndFiles.DATA)

    hardlink_tree(src=analysis_data, dst=destination)


def mark_as_demultiplexed(flow_cell_dir: Path) -> None:
    Path(flow_cell_dir, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()


def mark_flow_cell_as_queued_for_post_processing(flow_cell_dir: Path) -> None:
    Path(flow_cell_dir, DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING).touch()


def hardlink_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src=src, dst=dst, copy_function=os.link)


def is_ready_for_post_processing(flow_cell_dir: Path, demultiplexed_runs: Path) -> bool:
    analysis: Path = get_latest_analysis_directory(flow_cell_dir)

    if not analysis:
        return False

    copy_completed = is_copied(analysis)
    analysis_completed = is_analyzed(analysis)
    in_demultiplexed_runs = is_in_demultiplexed_runs(flow_cell_dir, demultiplexed_runs)
    post_processed = is_queued_for_post_processing(flow_cell_dir)

    return (
        copy_completed and analysis_completed and not in_demultiplexed_runs and not post_processed
    )
