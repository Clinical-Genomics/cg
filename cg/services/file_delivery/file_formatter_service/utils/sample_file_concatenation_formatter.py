from pathlib import Path

from cg.constants.constants import ReadDirection, FileFormat, FileExtensions
from cg.meta.deliver.fastq_path_generator import generate_concatenated_fastq_delivery_path
from cg.services.file_delivery.fetch_file_service.models import SampleFile
from cg.services.file_delivery.file_formatter_service.models import FormattedFile
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)


class SampleFileConcatenationFormatter(SampleFileFormatter):

    def format_files(
        self, sample_files: list[SampleFile], ticket_dir_path: Path
    ) -> list[FormattedFile]:
        formatted_files: list[FormattedFile] = super().format_files(
            sample_files=sample_files, ticket_dir_path=ticket_dir_path
        )
        forward_paths, reverse_path = self._concatenate_fastq_files(formatted_files=formatted_files)
        return self._replace_fastq_paths(
            reverse_paths=reverse_path,
            forward_paths=forward_paths,
            formatted_files=formatted_files,
        )

    def _concatenate_fastq_files(
        self, formatted_files: list[FormattedFile]
    ) -> tuple[list[Path], list[Path]]:
        unique_sample_dir_paths: set[Path] = self._get_unique_sample_paths(
            sample_files=formatted_files
        )
        forward_paths: list[Path] = []
        reverse_paths: list[Path] = []
        for sample_dir_path in unique_sample_dir_paths:
            sample_name: str = sample_dir_path.name
            forward_path: Path = generate_concatenated_fastq_delivery_path(
                fastq_directory=sample_dir_path,
                sample_name=sample_name,
                direction=ReadDirection.FORWARD,
            )
            forward_paths.append(forward_path)
            reverse_path: Path = generate_concatenated_fastq_delivery_path(
                fastq_directory=sample_dir_path,
                sample_name=sample_name,
                direction=ReadDirection.REVERSE,
            )
            reverse_paths.append(reverse_path)
            self.concatenation_service.concatenate(
                fastq_directory=sample_dir_path,
                forward_output_path=forward_path,
                reverse_output_path=reverse_path,
                remove_raw=True,
            )
        return forward_paths, reverse_paths

    @staticmethod
    def _get_unique_sample_paths(sample_files: list[FormattedFile]) -> set[Path]:
        sample_paths: list[Path] = []
        for sample_file in sample_files:
            sample_paths.append(sample_file.formatted_path)
        return set(sample_paths)

    @staticmethod
    def _replace_fastq_formatted_file_path(
        formatted_files: list[FormattedFile],
        direction: ReadDirection,
        new_path: Path,
    ):
        for formatted_file in formatted_files:
            if (
                formatted_file.formatted_path.parent == new_path.parent
                and f"{FileFormat.FASTQ}{FileExtensions.GZIP}" in formatted_file.formatted_path.name
                and f"R{direction}" in formatted_file.formatted_path.name
            ):
                formatted_file.formatted_path = new_path
        return formatted_files

    def _replace_fastq_paths(
        self,
        forward_paths: list[Path],
        reverse_paths: list[Path],
        formatted_files: list[FormattedFile],
    ) -> list[FormattedFile]:
        for forward_path in forward_paths:
            formatted_files = self._replace_fastq_formatted_file_path(
                formatted_files=formatted_files,
                direction=ReadDirection.FORWARD,
                new_path=forward_path,
            )
        for reverse_path in reverse_paths:
            formatted_files = self._replace_fastq_formatted_file_path(
                formatted_files=formatted_files,
                direction=ReadDirection.REVERSE,
                new_path=reverse_path,
            )
        return formatted_files
