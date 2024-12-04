from pathlib import Path

from cg.apps.lims import LimsAPI
from cg.constants.constants import ReadDirection, FileFormat, FileExtensions
from cg.services.deliver_files.file_formatter.utils.models import FastqFile

from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.fastq_concatenation_service.utils import generate_concatenated_fastq_delivery_path
from cg.services.deliver_files.file_fetcher.models import SampleFile
from cg.services.deliver_files.file_formatter.models import FormattedFile
from cg.services.deliver_files.file_formatter.utils.sample_service import (
    NestedSampleFileNameFormatter,
    FileManager,
    FlatSampleFileNameFormatter,
)
from cg.utils.files import get_all_files_in_directory_tree


class SampleFileConcatenationFormatter:
    """
    Format the sample files to deliver, concatenate fastq files and return the formatted files.
    Used for workflows: Microsalt.
    """

    def __init__(
        self,
        file_manager: FileManager,
        file_formatter: NestedSampleFileNameFormatter | FlatSampleFileNameFormatter,
        concatenation_service: FastqConcatenationService,
    ):
        self.file_manager = file_manager
        self.file_name_formatter = file_formatter
        self.concatenation_service = concatenation_service

    def format_files(
        self, moved_files: list[SampleFile], delivery_path: Path
    ) -> list[FormattedFile]:
        """Format the sample files to deliver, concatenate fastq files and return the formatted files."""
        sample_names: set[str] = self.file_name_formatter.get_sample_names(sample_files=moved_files)
        self._create_sample_directories(delivery_path=delivery_path, sample_names=sample_names)
        formatted_files: list[FormattedFile] = self.file_name_formatter.format_sample_file_names(
            sample_files=moved_files
        )
        for formatted_file in formatted_files:
            self.file_manager.rename_file(
                src=formatted_file.original_path, dst=formatted_file.formatted_path
            )
        forward_paths, reverse_path = self._concatenate_fastq_files(
            delivery_path=delivery_path,
            sample_names=sample_names,
        )
        self._replace_fastq_paths(
            reverse_paths=reverse_path,
            forward_paths=forward_paths,
            formatted_files=formatted_files,
        )
        return formatted_files

    def _create_sample_directories(self, sample_names: set[str], delivery_path: Path) -> None:
        """Create directories for each sample name only if the file name formatter is the NestedSampleFileFormatter.
        args:
            sample_names: set[str]: Set of sample names.
            delivery_path: Path: Path to the delivery directory.
        """
        if not isinstance(self.file_name_formatter, NestedSampleFileNameFormatter):
            return
        for sample_name in sample_names:
            self.file_manager.create_directories(base_path=delivery_path, directories={sample_name})

    def _concatenate_fastq_files(
        self, delivery_path: Path, sample_names: set[str]
    ) -> tuple[list[Path], list[Path]]:
        fastq_files: list[FastqFile] = self._get_unique_sample_fastq_paths(
            sample_names=sample_names, delivery_path=delivery_path
        )
        grouped_fastq_files: dict[str, list[FastqFile]] = self._group_fastq_files_per_sample(
            sample_names=sample_names, fastq_files=fastq_files
        )
        forward_paths: list[Path] = []
        reverse_paths: list[Path] = []

        # Generate  one forward and one reverse path for each sample
        for sample in grouped_fastq_files.keys():
            fastq_directory: Path = grouped_fastq_files[sample][0].fastq_file_path.parent
            forward_path: Path = generate_concatenated_fastq_delivery_path(
                fastq_directory=fastq_directory,
                sample_name=sample,
                direction=ReadDirection.FORWARD,
            )
            forward_paths.append(forward_path)
            reverse_path: Path = generate_concatenated_fastq_delivery_path(
                fastq_directory=fastq_directory,
                sample_name=sample,
                direction=ReadDirection.REVERSE,
            )
            reverse_paths.append(reverse_path)
            self.concatenation_service.concatenate(
                sample_id=sample,
                fastq_directory=fastq_directory,
                forward_output_path=forward_path,
                reverse_output_path=reverse_path,
                remove_raw=True,
            )
        return forward_paths, reverse_paths

    @staticmethod
    def _get_unique_sample_fastq_paths(
        sample_names: set[str], delivery_path: Path
    ) -> list[FastqFile]:
        """Get a list of unique sample fastq file paths given a delivery path."""
        sample_paths: list[FastqFile] = []
        list_of_files: list[Path] = get_all_files_in_directory_tree(delivery_path)
        for sample_name in sample_names:
            for file in list_of_files:
                if (
                    sample_name in file.as_posix()
                    and f"{FileFormat.FASTQ}{FileExtensions.GZIP}" in file.as_posix()
                ):
                    sample_paths.append(
                        FastqFile(
                            fastq_file_path=Path(delivery_path, file), sample_name=sample_name
                        )
                    )
        return sample_paths

    def _group_fastq_files_per_sample(
        self, sample_names: set[str], fastq_files: list[FastqFile]
    ) -> dict[str, list[FastqFile]]:
        """Group fastq files per sample."""
        sample_fastq_files: dict[str, list[FastqFile]] = {
            sample_name: [] for sample_name in sample_names
        }
        for fastq_file in fastq_files:
            sample_fastq_files[fastq_file.sample_name].append(fastq_file)
        self._all_sample_fastq_file_share_same_directory(sample_fastq_files=sample_fastq_files)
        return sample_fastq_files

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

    @staticmethod
    def _all_sample_fastq_file_share_same_directory(
        sample_fastq_files: dict[str, list[FastqFile]]
    ) -> None:
        """
        Assert that all fastq files for a sample share the same directory.
        args:
            sample_fastq_files: dict[str, list[FastqFile]]: Dictionary of sample names and their fastq files.
        """
        for sample_name in sample_fastq_files.keys():
            fastq_files: list[FastqFile] = sample_fastq_files[sample_name]
            parent_dir: Path = fastq_files[0].fastq_file_path.parent
            for fastq_file in fastq_files:
                if fastq_file.fastq_file_path.parent != parent_dir:
                    raise ValueError(
                        f"Sample {sample_name} fastq files are not in the same directory. "
                        f"Cannot concatenate. It will would result in sporadic file paths."
                    )
