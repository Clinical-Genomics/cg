import re
from pathlib import Path


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

