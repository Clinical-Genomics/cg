from pathlib import Path

from cg.services.fastq_file_service.utils import (
    get_concatenated_reverse_read_output_path,
    get_concatenated_forward_read_output_path,
    concatenate_forward_reads,
    concatenate_reverse_reads,
    remove_raw_fastqs,
)


class FastqFileService:
    def concatenate(
        self,
        fastq_directory: Path,
        sample_name: str,
        remove_raw: bool = False,
    ):
        forward_output: Path = get_concatenated_forward_read_output_path(
            fastq_directory=fastq_directory, sample_name=sample_name
        )
        reverse_output: Path = get_concatenated_reverse_read_output_path(
            fastq_directory=fastq_directory, sample_name=sample_name
        )
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
