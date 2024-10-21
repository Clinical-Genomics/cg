from pathlib import Path

from cg.constants.constants import ReadDirection, FileFormat, FileExtensions

from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.fastq_concatenation_service.utils import generate_concatenated_fastq_delivery_path
from cg.services.deliver_files.file_fetcher.models import SampleFile
from cg.services.deliver_files.file_formatter.models import FormattedFile
from cg.services.deliver_files.file_formatter.utils.sample_service import (
    SampleFileFormatter,
)


class SampleFileConcatenationFormatter(SampleFileFormatter):
    """
    Format the sample files to deliver, concatenate fastq files and return the formatted files.
    Used for workflows: Microsalt and Mutant.
    """

    def __init__(self, concatenation_service: FastqConcatenationService):
        self.concatenation_service = concatenation_service

    def format_files(
        self, moved_files: list[SampleFile], ticket_dir_path: Path
    ) -> list[FormattedFile]:
        """Format the sample files to deliver, concatenate fastq files and return the formatted files."""
        formatted_files: list[FormattedFile] = super().format_files(
            moved_files=moved_files, ticket_dir_path=ticket_dir_path
        )
        forward_paths, reverse_path = self._concatenate_fastq_files(formatted_files=formatted_files)
        self._replace_fastq_paths(
            reverse_paths=reverse_path,
            forward_paths=forward_paths,
            formatted_files=formatted_files,
        )
        return formatted_files

    def _concatenate_fastq_files(
        self, formatted_files: list[FormattedFile]
    ) -> tuple[list[Path], list[Path]]:
        unique_sample_dir_paths: set[Path] = self._get_unique_sample_paths(
            sample_files=formatted_files
        )
        forward_paths: list[Path] = []
        reverse_paths: list[Path] = []
        for fastq_directory in unique_sample_dir_paths:
            sample_name: str = fastq_directory.name

            forward_path: Path = generate_concatenated_fastq_delivery_path(
                fastq_directory=fastq_directory,
                sample_name=sample_name,
                direction=ReadDirection.FORWARD,
            )
            forward_paths.append(forward_path)
            reverse_path: Path = generate_concatenated_fastq_delivery_path(
                fastq_directory=fastq_directory,
                sample_name=sample_name,
                direction=ReadDirection.REVERSE,
            )
            reverse_paths.append(reverse_path)
            self.concatenation_service.concatenate(
                fastq_directory=fastq_directory,
                forward_output_path=forward_path,
                reverse_output_path=reverse_path,
                remove_raw=True,
            )
        return forward_paths, reverse_paths

    @staticmethod
    def _get_unique_sample_paths(sample_files: list[FormattedFile]) -> set[Path]:
        sample_paths: list[Path] = []
        for sample_file in sample_files:
            sample_paths.append(sample_file.formatted_path.parent)
        return set(sample_paths)

    @staticmethod
    def _replace_fastq_formatted_file_path(
        formatted_files: list[FormattedFile],
        direction: ReadDirection,
        new_path: Path,
    ) -> None:
        """Replace the formatted file path with the new path."""
        for formatted_file in formatted_files:
            if (
                formatted_file.formatted_path.parent == new_path.parent
                and f"{FileFormat.FASTQ}{FileExtensions.GZIP}" in formatted_file.formatted_path.name
                and f"R{direction}" in formatted_file.formatted_path.name
            ):
                formatted_file.formatted_path = new_path

    def _replace_fastq_paths(
        self,
        forward_paths: list[Path],
        reverse_paths: list[Path],
        formatted_files: list[FormattedFile],
    ) -> None:
        """Replace the fastq file paths with the new concatenated fastq file paths."""
        for forward_path in forward_paths:
            self._replace_fastq_formatted_file_path(
                formatted_files=formatted_files,
                direction=ReadDirection.FORWARD,
                new_path=forward_path,
            )
        for reverse_path in reverse_paths:
            self._replace_fastq_formatted_file_path(
                formatted_files=formatted_files,
                direction=ReadDirection.REVERSE,
                new_path=reverse_path,
            )
