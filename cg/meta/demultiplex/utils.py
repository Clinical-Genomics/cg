import logging
import os
import re
from pathlib import Path
from typing import List, Optional
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.exc import FlowCellError
from cg.meta.demultiplex.validation import (
    is_bcl2fastq_demux_folder_structure,
    is_flow_cell_directory_valid,
    validate_sample_fastq_file,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData

LOG = logging.getLogger(__name__)


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


def create_delivery_file_in_flow_cell_directory(flow_cell_directory: Path) -> None:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()


def get_sample_ids_from_sample_sheet(flow_cell_data: FlowCellDirectoryData) -> List[str]:
    samples: List[FlowCellSample] = flow_cell_data.get_sample_sheet().samples
    sample_ids_with_indexes: List[str] = [sample.sample_id for sample in samples]
    return [sample_id_index.split("_")[0] for sample_id_index in sample_ids_with_indexes]


def get_q30_threshold(sequencer_type: Sequencers) -> int:
    return FLOWCELL_Q30_THRESHOLD[sequencer_type]


def get_valid_sample_fastq_paths(flow_cell_directory: Path):
    """Get all valid sample fastq file paths from flow cell directory."""
    fastq_file_paths: List[Path] = get_sample_fastq_paths_from_flow_cell(flow_cell_directory)
    valid_sample_fastq_paths: List[Path] = []

    for fastq_path in fastq_file_paths:
        try:
            validate_sample_fastq_file(fastq_path)
            valid_sample_fastq_paths.append(fastq_path)
        except ValueError as e:
            LOG.warning(f"Skipping invalid sample fastq file {fastq_path.name}: {e}")

    return valid_sample_fastq_paths


def get_sample_sheet_path(flow_cell_directory: Path) -> Optional[Path]:
    """
    Recursively searches for the given sample sheet file in the provided flow cell directory.

    Raises:
        FileNotFoundError: If the sample sheet file is not found in the flow cell directory.
    """
    for directory_path, _, files in os.walk(flow_cell_directory):
        if DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME in files:
            LOG.info(f"Found sample sheet in {directory_path}")
            return Path(directory_path, DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)

    raise FileNotFoundError(
        f"Sample sheet not found in given flow cell directory: {flow_cell_directory}"
    )


def parse_flow_cell_directory_data(
    flow_cell_directory: Path, bcl_converter: str
) -> FlowCellDirectoryData:
    """Parse flow cell data from the flow cell directory."""

    if not is_flow_cell_directory_valid(flow_cell_directory):
        raise FlowCellError(f"Flow cell directory was not valid: {flow_cell_directory}")

    return FlowCellDirectoryData(flow_cell_path=flow_cell_directory, bcl_converter=bcl_converter)
