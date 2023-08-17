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


def is_queued_for_post_processing(flow_cell: Path) -> bool:
    return Path(flow_cell, DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING).exists()


def copy_flow_cell_analysis_data(flow_cell: Path, destination: Path) -> None:
    analysis = get_latest_analysis_directory(flow_cell)
    analysis_data = Path(analysis, DemultiplexingDirsAndFiles.DATA)

    hardlink_tree(src=analysis_data, dst=destination)


def mark_as_demultiplexed(flow_cell: Path) -> None:
    Path(flow_cell, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).touch()


def mark_flow_cell_as_queued_for_post_processing(flow_cell: Path) -> None:
    Path(flow_cell, DemultiplexingDirsAndFiles.QUEUED_FOR_POST_PROCESSING).touch()


def hardlink_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, copy_function=os.link)


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
