from pathlib import Path

from cg.services.fastq_file_service.utils import (
    concatenate_forward_reads,
    concatenate_reverse_reads,
    remove_raw_fastqs,
)


class FastqFileService:

    def concatenate(
        self,
        fastq_directory: Path,
        forward_output: Path,
        reverse_output: Path,
        remove_raw: bool = False,
    ):
        concatenate_forward_reads(directory=fastq_directory, output_file=forward_output)
        concatenate_reverse_reads(directory=fastq_directory, output_file=reverse_output)

        if remove_raw:
            remove_raw_fastqs()
