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
        temp_forward: Path | None = concatenate_forward_reads(fastq_directory)
        temp_reverse: Path | None = concatenate_reverse_reads(fastq_directory)

        if remove_raw:
            remove_raw_fastqs(
                fastq_directory=fastq_directory,
                forward_file=temp_forward,
                reverse_file=temp_reverse,
            )

        if temp_forward:
            temp_forward.rename(forward_output)

        if temp_reverse:
            temp_reverse.rename(reverse_output)
