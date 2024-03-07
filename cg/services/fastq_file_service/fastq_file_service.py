from pathlib import Path

from cg.services.fastq_file_service.utils import (
    get_concatenated_read_output_path,
    concatenate_forward_reads,
    concatenate_reverse_reads,
    remove_raw_fastqs,
)
from cg.constants.constants import ReadDirection


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

    @staticmethod
    def get_concatenated_forward_read_output_path(fastq_directory: Path, sample_name: str) -> Path:
        return get_concatenated_read_output_path(
            fastq_directory=fastq_directory,
            sample_name=sample_name,
            direction=ReadDirection.FORWARD,
        )

    @staticmethod
    def get_concatenated_reverse_read_output_path(fastq_directory: Path, sample_name: str) -> Path:
        return get_concatenated_read_output_path(
            fastq_directory=fastq_directory,
            sample_name=sample_name,
            direction=ReadDirection.REVERSE,
        )
