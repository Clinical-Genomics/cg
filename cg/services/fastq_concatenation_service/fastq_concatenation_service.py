import logging
from pathlib import Path

from cg.constants.constants import ReadDirection
from cg.services.fastq_concatenation_service.utils import (
    remove_raw_fastqs,
    concatenate_fastq_reads_for_direction,
)

LOG = logging.getLogger(__name__)


class FastqConcatenationService:
    """Fastq file concatenation service."""

    @staticmethod
    def concatenate(
        sample_id: str,
        fastq_directory: Path,
        forward_output_path: Path,
        reverse_output_path: Path,
        remove_raw: bool = False,
    ):
        """Concatenate fastq files for a given sample in a directory and write the concatenated files to the output path.

        Args:
            sample_id: The identifier to identify the samples by it should be a unique identifier in the file name.
            fastq_directory: The directory containing the fastq files.
            forward_output_path: The path where the concatenated forward reads will be written.
            reverse_output_path: The path where the concatenated reverse reads will be written.
            remove_raw: If True, remove the raw fastq files after concatenation.
        """
        LOG.debug(
            f"[Concatenation Service] Concatenating fastq files for {sample_id} in {fastq_directory}"
        )
        temp_forward: Path | None = concatenate_fastq_reads_for_direction(
            directory=fastq_directory, sample_id=sample_id, direction=ReadDirection.FORWARD
        )
        temp_reverse: Path | None = concatenate_fastq_reads_for_direction(
            directory=fastq_directory, sample_id=sample_id, direction=ReadDirection.REVERSE
        )

        if remove_raw:
            remove_raw_fastqs(
                sample_id=sample_id,
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
