import logging
import re

from pathlib import Path
from typing import List, Optional


from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.meta.demultiplex.validation import (
    is_valid_sample_fastq_file,
)
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData

from cg.utils.files import (
    get_file_in_directory,
    get_files_matching_pattern,
    is_pattern_in_file_path_name,
    rename_file,
)

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
    """Retrieve all fastq files for a specific sample in a flow cell directory."""

    # The flat output structure for NovaseqX flow cells demultiplexed with bclconvert on hasta
    root_pattern = f"{sample_internal_id}_S*_L*_R*_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"

    # The default structure for flow cells demultiplexed with bcl2fastq
    unaligned_pattern = f"Unaligned*/Project_*/Sample_{sample_internal_id}/*{FileExtensions.FASTQ}{FileExtensions.GZIP}"

    # Alternative structure for flow cells demultiplexed with bcl2fastq where the sample fastq files have a trailing sequence
    unaligned_alt_pattern = f"Unaligned*/Project_*/Sample_{sample_internal_id}_*/*{FileExtensions.FASTQ}{FileExtensions.GZIP}"

    # The default structure for flow cells demultiplexed with bclconvert
    bcl_convert_pattern = (
        f"Unaligned*/*/{sample_internal_id}_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )

    # The pattern for novaseqx flow cells demultiplexed on board of the dragen
    demux_on_sequencer_pattern = f"BCLConvert/fastq/{sample_internal_id}_S*_L*_R*_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"

    for pattern in [
        root_pattern,
        unaligned_pattern,
        unaligned_alt_pattern,
        bcl_convert_pattern,
        demux_on_sequencer_pattern,
    ]:
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


def create_delivery_file_in_flow_cell_directory(flow_cell_directory: Path) -> None:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()


def get_q30_threshold(sequencer_type: Sequencers) -> int:
    return FLOWCELL_Q30_THRESHOLD[sequencer_type]


def get_sample_sheet_path(
    flow_cell_directory: Path,
    sample_sheet_file_name: str = DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME,
) -> Path:
    """Return the path to the sample sheet in the flow cell directory."""
    return get_file_in_directory(directory=flow_cell_directory, file_name=sample_sheet_file_name)


def parse_flow_cell_directory_data(
    flow_cell_directory: Path, bcl_converter: Optional[str] = None
) -> FlowCellDirectoryData:
    """Return flow cell data from the flow cell directory."""
    return FlowCellDirectoryData(flow_cell_path=flow_cell_directory, bcl_converter=bcl_converter)


def add_flow_cell_name_to_fastq_file_path(fastq_file_path: Path, flow_cell_name: str) -> Path:
    """Add the flow cell name to the fastq file path if the flow cell name is not already in the given file path."""
    if is_pattern_in_file_path_name(file_path=fastq_file_path, pattern=flow_cell_name):
        LOG.debug(
            f"Flow cell name {flow_cell_name} already in {fastq_file_path}. Skipping renaming."
        )
        return fastq_file_path
    LOG.debug(f"Adding flow cell name {flow_cell_name} to {fastq_file_path}.")
    return Path(fastq_file_path.parent, f"{flow_cell_name}_{fastq_file_path.name}")


def rename_fastq_file_if_needed(fastq_file_path: Path, flow_cell_name: str) -> Path:
    """Rename the given fastq file path if the renamed fastq file path does not exist."""
    renamed_fastq_file_path: Path = add_flow_cell_name_to_fastq_file_path(
        fastq_file_path=fastq_file_path, flow_cell_name=flow_cell_name
    )
    if fastq_file_path != renamed_fastq_file_path:
        rename_file(file_path=fastq_file_path, renamed_file_path=renamed_fastq_file_path)
    return renamed_fastq_file_path
