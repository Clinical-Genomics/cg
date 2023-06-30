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
    return int(sample_fastq_path.name.split("_")[3])


def get_sample_id_from_sample_fastq_path(fastq_file_path: Path) -> str:
    """
    Extract sample id from fastq file path.
    Pre-condition:
        - The fastq file path exists.
        - The sample id is the second part of the directory name.
    """
    sample_directory: str = fastq_file_path.parent.name
    directory_parts: List[str] = sample_directory.split("_")

    if len(directory_parts) > 1:
        return directory_parts[1]

    return directory_parts[0]
