import os
from pathlib import Path
import re


def validate_sample_fastq_file(sample_fastq: Path) -> None:
    """
    This function validates that the sample fastq file name is formatted as expected.

    Since many different naming conventions are used, these are the only assumptions which can be made:
    1. The sample fastq file name ends with .fastq.gz
    2. The sample fastq file name contains the lane number formatted as _L<lane_number>
    3. The sample fastq file is located in a directory containing the sample id formatted as Sample_<sample_id>
    """

    # Check that file name ends with .fastq.gz
    if not sample_fastq.name.endswith(".fastq.gz"):
        raise ValueError("Sample fastq must end with '.fastq.gz'.")

    # Check that file name contains lane number formatted as _L<lane_number>
    if not re.search(r"_L\d+", sample_fastq.name):
        raise ValueError("Sample fastq must contain lane number formatted as '_L<lane_number>'.")

    # Check that directory name contains Sample_<sample_id>
    if not re.search(r"Sample_\d+", sample_fastq.parent.name):
        raise ValueError("Directory name must contain 'Sample_<sample_id>'.")
