import logging
from pathlib import Path

from cg.services.fastq_concatenation_service.utils import (
    concatenate_forward_reads,
    concatenate_reverse_reads,
    remove_raw_fastqs,
)

LOG = logging.getLogger(__name__)


class FastqConcatenationService:

    def concatenate(
        self,
        fastq_directory: Path,
        forward_output_path: Path,
        reverse_output_path: Path,
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
            LOG.info(f"Concatenated forward reads to {forward_output_path}")
            temp_forward.rename(forward_output_path)

        if temp_reverse:
            LOG.info(f"Concatenated reverse reads to {reverse_output_path}")
            temp_reverse.rename(reverse_output_path)
