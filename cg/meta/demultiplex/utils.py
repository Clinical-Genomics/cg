from pathlib import Path
from typing import List


def get_flow_cell_name_from_sample_fastq(sample_fastq_path: Path) -> str:
    """
    Extract the flow cell name from the sample fastq path.

    Pre-condition:
        - The third part of the sample fastq file name is the lane number.
    """
    return sample_fastq_path.name.split("_")[0]


def get_lane_from_sample_fastq(sample_fastq_path: Path) -> int:
    """
    Extract the lane number from the sample fastq path.

    Pre-condition:
        - The third part of the sample fastq file name is the lane number.
    """
    lane_part = sample_fastq_path.name.split("_")[3]
    return int(lane_part[1:])  # Skip the lane indicator 'L'


def get_sample_id_from_sample_fastq(sample_fastq: Path) -> str:
    """
    Extract sample id from fastq file path.
    Pre-condition:
        - The sample id is the second part of the sample fastq name.
    """
    return sample_fastq.name.split("_")[1]
