import re
from pathlib import Path


def get_lane_from_sample_fastq(sample_fastq_path: Path) -> int:
    """
    Extract the lane number from the sample fastq path.

    Pre-condition:
        - The fastq file name is in the format [<flow_cell_id>_]<sample_id>_<sample_index>_S<set_number>_L<lane_number>_R<read_number>_<segement_number>.fastq.gz
    """
    pattern = r"_L(\d+)_"
    lane_match = re.search(pattern, sample_fastq_path.name)

    if lane_match:
        return int(lane_match.group(1))

    raise ValueError(f"Could not extract lane number from fastq file name {sample_fastq_path.name}")


def get_sample_id_from_sample_fastq(sample_fastq: Path) -> str:
    """
    Extract sample id from fastq file path.

    Pre-condition:
        - The fastq file name is in the format [<flow_cell_id>_]<sample_id>_<sample_index>_S<set_number>_L<lane_number>_R<read_number>_<segement_number>.fastq.gz
    """
    pattern = r"^(.*_)?([^_]*_S\d+)_.*$"  # Captures everything before `_S` as a whole (flow cell and sample id)
    match = re.search(pattern, sample_fastq.name)

    if match:
        return match.group(2).split("_S")[0]  # Returns only the sample id part

    raise ValueError(f"Could not extract sample id from fastq file name {sample_fastq.name}")
