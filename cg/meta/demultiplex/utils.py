import re
from pathlib import Path
from typing import List

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles


def get_lane_from_sample_fastq(sample_fastq_path: Path) -> int:
    """
    Extract the lane number from the sample fastq path.
    Pre-condition:
        - The fastq file name contains the lane number formatted as _L<lane_number>
    """
    pattern = r"_L(\d+)"
    lane_match = re.search(pattern, sample_fastq_path.name)

    if lane_match:
        return int(lane_match.group(1))

    raise ValueError(f"Could not extract lane number from fastq file name {sample_fastq_path.name}")


def get_sample_id_from_sample_fastq(sample_fastq: Path) -> str:
    """
    Extract sample id from fastq file path.

    Pre-condition:
        - The parent directory name contains the sample id formatted as Sample_<sample_id>
    """

    sample_parent_match = re.search(r"Sample_(\w+)", sample_fastq.parent.name)

    if sample_parent_match:
        return sample_parent_match.group(1)
    else:
        raise ValueError("Parent directory name does not contain 'Sample_<sample_id>'.")


def get_sample_fastq_paths_from_flow_cell(flow_cell_directory: Path) -> List[Path]:
    fastq_sample_pattern: str = (
        f"Unaligned*/Project_*/Sample_*/*{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )
    return list(flow_cell_directory.glob(fastq_sample_pattern))


def get_bcl_converter_name(flow_cell_directory: Path) -> str:
    if is_bcl2fastq_demux_folder_structure(flow_cell_directory=flow_cell_directory):
        return BclConverter.BCL2FASTQ
    return BclConverter.BCLCONVERT


def is_bcl2fastq_demux_folder_structure(flow_cell_directory: Path) -> bool:
    """Check if flow cell directory is a Bcl2fastq demux folder structure."""
    for folder in flow_cell_directory.glob(pattern="*"):
        if re.search(DemultiplexingDirsAndFiles.BCL2FASTQ_TILE_DIR_PATTERN.value, str(folder)):
            return True
    return False
