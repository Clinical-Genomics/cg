import re
from pathlib import Path
from typing import List
from cg.apps.demultiplex.sample_sheet.models import FlowCellSample

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import BclConverter, DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.meta.demultiplex.validation import is_bcl2fastq_demux_folder_structure
from cg.models.demultiplex.flow_cell import FlowCellDirectoryData


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
