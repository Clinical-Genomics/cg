import re
from pathlib import Path
import logging
from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.exc import FlowCellError
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)


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
    """Validate that directory name contains the sample id formatted as Sample_<sample_id> or Sample_<sample_id>_."""
    sample_pattern: str = f"Sample_{sample_internal_id}"
    return f"{sample_pattern}_" in directory.name or sample_pattern == directory.name


def is_sample_id_in_file_name(sample_fastq: Path, sample_internal_id: str) -> bool:
    """Validate that file name contains the sample id formatted as <sample_id>_."""
    return f"{sample_internal_id}_" in sample_fastq.name


def is_demultiplexing_complete(flow_cell_directory: Path) -> bool:
    return Path(flow_cell_directory, DemultiplexingDirsAndFiles.DEMUX_COMPLETE).exists()


def is_flow_cell_ready_for_delivery(flow_cell_directory: Path) -> bool:
    return Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).exists()


def validate_sample_sheet_exists(flow_cell: FlowCellDirectoryData) -> None:
    sample_sheet_path: Path = flow_cell.get_sample_sheet_path_hk()
    if not sample_sheet_path or not sample_sheet_path.exists():
        raise FlowCellError(f"Sample sheet {sample_sheet_path} does not exist in housekeeper.")
    LOG.debug(f"Found sample sheet {sample_sheet_path} in housekeeper.")


def validate_demultiplexing_complete(flow_cell_output_directory: Path) -> None:
    if not is_demultiplexing_complete(flow_cell_output_directory):
        raise FlowCellError(
            f"Demultiplexing not completed for flow cell directory {flow_cell_output_directory}."
        )


def validate_flow_cell_delivery_status(flow_cell_output_directory: Path, force: bool) -> None:
    if is_flow_cell_ready_for_delivery(flow_cell_output_directory) and not force:
        raise FlowCellError(
            f"Flow cell output directory {flow_cell_output_directory} has already been processed and is ready for delivery."
        )
    return


def is_flow_cell_ready_for_postprocessing(
    flow_cell_output_directory: Path,
    flow_cell: FlowCellDirectoryData,
    force: bool = False,
) -> None:
    validate_sample_sheet_exists(flow_cell)
    validate_demultiplexing_complete(flow_cell_output_directory)
    validate_flow_cell_delivery_status(flow_cell_output_directory, force=force)
