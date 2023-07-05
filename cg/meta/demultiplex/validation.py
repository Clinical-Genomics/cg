import re
from pathlib import Path

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import INDEX_CHECK, DemultiplexingDirsAndFiles
from cg.exc import FlowCellError


def validate_sample_fastq_file(sample_fastq: Path) -> None:
    """
    Validate that the sample fastq file name is formatted as expected.

    Since many different naming conventions are used, these are the only assumptions which can be made:
    1. The sample fastq file name ends with .fastq.gz
    2. The sample fastq file name contains the lane number formatted as _L<lane_number>
    3. The sample fastq file is located in a directory containing the sample id formatted as Sample_<sample_id>
    """

    if not is_file_path_compressed_fastq(sample_fastq):
        raise ValueError(f"Sample fastq must end with {FileExtensions.FASTQ}{FileExtensions.GZIP}.")

    if not is_lane_in_fastq_file_name(sample_fastq):
        raise ValueError("Sample fastq must contain lane number formatted as '_L<lane_number>'.")

    if not is_sample_id_in_directory_name(sample_fastq.parent):
        raise ValueError("Parent directory name of sample fastq must contain 'Sample_<sample_id>'.")


def is_file_path_compressed_fastq(file_path: Path) -> bool:
    return file_path.name.endswith(f"{FileExtensions.FASTQ}{FileExtensions.GZIP}")


def is_lane_in_fastq_file_name(sample_fastq: Path) -> bool:
    """Validate that fastq contains lane number formatted as _L<lane_number>"""
    return bool(re.search(r"_L\d+", sample_fastq.name))


def is_sample_id_in_directory_name(directory: Path) -> bool:
    """Validate that directory name contains the sample id formatted as Sample_<sample_id>"""
    return bool(re.search(r"Sample_\w+", directory.name))


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
