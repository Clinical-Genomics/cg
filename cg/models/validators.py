from typing import List

from cg.exc import SampleSheetError


def fastq_files_exist(fastq_paths: List[str]) -> List[str]:
    """Verify that fastq files exist."""
    for fastq_path in fastq_paths:
        if not fastq_path.is_file():
            raise SampleSheetError(f"Fastq file does not exist: {str(fastq_path)}")
    return fastq_paths
