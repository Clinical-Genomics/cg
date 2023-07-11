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
    is_valid_sample_id,
    is_valid_sample_fastq_file,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData
from cg.utils.utils import get_files_matching_pattern

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


def get_sample_fastqs_from_flow_cell(
    flow_cell_directory: Path, sample_internal_id: str
) -> Optional[List[Path]]:
    """Retrieve sample FastQs from a flow cell directory."""
    root_pattern = f"{sample_internal_id}_S*_L*_R*_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    unaligned_pattern = f"Unaligned*/Project_*/Sample_{sample_internal_id}*/*{FileExtensions.FASTQ}{FileExtensions.GZIP}"

    for pattern in [root_pattern, unaligned_pattern]:
        sample_fastqs: List[Path] = get_files_matching_pattern(
            directory=flow_cell_directory, pattern=pattern
        )
        valid_sample_fastqs: List[Path] = get_valid_sample_fastqs(
            fastq_paths=sample_fastqs, sample_internal_id=sample_internal_id
        )

        if valid_sample_fastqs:
            return valid_sample_fastqs


def get_valid_sample_fastqs(fastq_paths: List[Path], sample_internal_id: str) -> List[Path]:
    """Return a list of valid fastq files."""
    return [
        fastq
        for fastq in fastq_paths
        if is_valid_sample_fastq_file(sample_fastq=fastq, sample_internal_id=sample_internal_id)
    ]


def get_bcl_converter_name(flow_cell_directory: Path) -> str:
    if is_bcl2fastq_demux_folder_structure(flow_cell_directory=flow_cell_directory):
        return BclConverter.BCL2FASTQ
    return BclConverter.BCLCONVERT


def create_delivery_file_in_flow_cell_directory(flow_cell_directory: Path) -> None:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()


def get_sample_internal_ids_from_flow_cell(flow_cell_data: FlowCellDirectoryData) -> List[str]:
    samples: List[FlowCellSample] = flow_cell_data.get_sample_sheet().samples
    return get_valid_sample_ids(samples)


def get_valid_sample_ids(samples: List[FlowCellSample]) -> List[str]:
    """Get all valid sample ids from sample sheet."""
    valid_sample_ids = [
        sample.sample_id for sample in samples if is_valid_sample_id(sample.sample_id)
    ]
    formatted_sample_ids = [sample_id_index.split("_")[0] for sample_id_index in valid_sample_ids]
    return formatted_sample_ids


def get_q30_threshold(sequencer_type: Sequencers) -> int:
    return FLOWCELL_Q30_THRESHOLD[sequencer_type]


def get_sample_sheet_path(flow_cell_directory: Path) -> Path:
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

    try:
        is_flow_cell_directory_valid(flow_cell_directory)
    except FlowCellError as e:
        raise FlowCellError(f"Flow cell directory was not valid: {flow_cell_directory}, {e}")

    return FlowCellDirectoryData(flow_cell_path=flow_cell_directory, bcl_converter=bcl_converter)
