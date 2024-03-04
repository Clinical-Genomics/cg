from pathlib import Path

from cg.services.fastq_file_service.utils import (
    concatenate_forward_reads,
    concatenate_reverse_reads,
    remove_raw_fastqs,
)
from cg.store.models import Case


class FastqFileService:

    @staticmethod
    def concatenate(
        fastq_directory: Path, sample_name: str, remove_raw: bool = False
    ) -> tuple[Path | None, Path | None]:
        """Concatenates forward and reverse reads into single files from a provided directory."""
        forward_out_path = Path(fastq_directory, f"{sample_name}_R1.fastq.gz")
        reverse_out_path = Path(fastq_directory, f"{sample_name}_R2.fastq.gz")
        temp_forward: Path | None = (
            concatenate_forward_reads(fastq_directory)
            if not forward_out_path.exists()
            else forward_out_path
        )
        temp_reverse: Path | None = (
            concatenate_reverse_reads(fastq_directory)
            if not reverse_out_path.exists()
            else reverse_out_path
        )
        if remove_raw:
            remove_raw_fastqs(
                fastq_directory=fastq_directory,
                forward_file=temp_forward,
                reverse_file=temp_reverse,
            )
        if temp_forward:
            temp_forward: Path = temp_forward.rename(forward_out_path)
        if temp_reverse:
            temp_reverse: Path = temp_reverse.rename(reverse_out_path)
        return temp_forward, temp_reverse

    @staticmethod
    def is_concatenation_needed(case: Case) -> bool:
        raise NotImplementedError
