import re
from pathlib import Path

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import INDEX_CHECK, DemultiplexingDirsAndFiles
from cg.exc import FlowCellError


def is_valid_sample_fastq_file(sample_fastq: Path, sample_internal_id: str) -> bool:
    """
    Validate that the sample fastq file name is formatted as expected.

    Assumptions:
    1. The sample fastq file name ends with .fastq.gz
    2. The sample fastq file name contains the lane number formatted as _L<lane_number>
    3. The sample internal id is present in the parent directory name or in the file name.
    """
    sample_id_in_directory: bool = is_sample_id_in_directory_name(
        directory=sample_fastq.parent, sample_internal_id=sample_internal_id
    )
    sample_id_in_file_name: bool = is_sample_id_in_file_name(
        sample_fastq=sample_fastq, sample_internal_id=sample_internal_id
    )

    return (
        is_file_path_compressed_fastq(sample_fastq)
        and is_lane_in_fastq_file_name(sample_fastq)
        and (sample_id_in_directory or sample_id_in_file_name)
    )


def is_file_path_compressed_fastq(file_path: Path) -> bool:
    return file_path.name.endswith(f"{FileExtensions.FASTQ}{FileExtensions.GZIP}")


def is_lane_in_fastq_file_name(sample_fastq: Path) -> bool:
    """Validate that fastq contains lane number formatted as _L<lane_number>"""
    return bool(re.search(r"_L\d+", sample_fastq.name))


def is_sample_id_in_directory_name(directory: Path, sample_internal_id: str) -> bool:
    """Validate that directory name contains the sample id formatted as Sample_<sample_id>."""
    return f"Sample_{sample_internal_id}" in directory.name


def is_sample_id_in_file_name(sample_fastq: Path, sample_internal_id: str) -> bool:
    """Validate that file name contains the sample id formatted as <sample_id>."""
    return sample_internal_id in sample_fastq.name


def is_bcl2fastq_demux_folder_structure(flow_cell_directory: Path) -> bool:
    """Check if flow cell directory is a Bcl2fastq demux folder structure."""
    for folder in flow_cell_directory.glob(pattern="*"):
        if re.search(DemultiplexingDirsAndFiles.BCL2FASTQ_TILE_DIR_PATTERN.value, str(folder)):
            return True
    return False


def is_flow_cell_directory_valid(flow_cell_directory: Path) -> None:
    """Validate that the flow cell directory exists and that the demultiplexing is complete."""

    if not flow_cell_directory.is_dir():
        raise FlowCellError(f"Flow cell directory {flow_cell_directory} does not exist.")

    if not is_demultiplexing_complete(flow_cell_directory):
        raise FlowCellError(
            f"Demultiplexing not completed for flow cell directory {flow_cell_directory}."
        )


def is_demultiplexing_complete(flow_cell_directory: Path) -> bool:
    return Path(flow_cell_directory, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()


def is_valid_sample_id(sample_id: str) -> bool:
    sample_id_is_index_check = INDEX_CHECK in sample_id
    sample_id_is_non_empty = bool(sample_id)
    return sample_id_is_non_empty and not sample_id_is_index_check
