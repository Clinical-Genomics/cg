import logging
from pathlib import Path
import re

from cg.constants.constants import ReadDirection, FileFormat, FileExtensions
from cg.services.deliver_files.file_formatter.files.abstract import FileFormatter
from cg.services.deliver_files.file_formatter.files.models import FastqFile
from cg.services.deliver_files.file_formatter.path_name.abstract import PathNameFormatter

from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.fastq_concatenation_service.utils import generate_concatenated_fastq_delivery_path
from cg.services.deliver_files.file_fetcher.models import SampleFile
from cg.services.deliver_files.file_formatter.destination.models import FormattedFile
from cg.services.deliver_files.file_formatter.files.sample_service import (
    FileManager,
)
from cg.services.deliver_files.file_formatter.path_name.nested_structure import (
    NestedStructurePathFormatter,
)
from cg.utils.files import get_all_files_in_directory_tree

LOG = logging.getLogger(__name__)


class SampleFileConcatenationFormatter(FileFormatter):
    """
    Format the sample files to deliver, concatenate fastq files and return the formatted files.
    Used for workflows: Microsalt.
    args:
        file_manager: The file manager
        path_name_formatter: The path name formatter to format paths to either a flat or nested structure in the delivery destination
        concatenation_service: The fastq concatenation service to concatenate fastq files.
    """

    def __init__(
        self,
        file_manager: FileManager,
        path_name_formatter: PathNameFormatter,
        concatenation_service: FastqConcatenationService,
    ):
        self.file_manager = file_manager
        self.path_name_formatter = path_name_formatter
        self.concatenation_service = concatenation_service

    def format_files(
        self, moved_files: list[SampleFile], delivery_path: Path
    ) -> list[FormattedFile]:
        """
        Format the sample files to deliver, concatenate fastq files and return the formatted files.
        args:
            moved_files: list[SampleFile]: List of sample files to deliver.
            These are files that have been moved from housekeeper to the delivery path.
            delivery_path: Path: Path to the delivery directory.
        """
        LOG.debug("[FORMAT SERVICE] Formatting and concatenating sample files")
        sample_names: set[str] = self._get_sample_names(sample_files=moved_files)
        self._create_sample_directories(delivery_path=delivery_path, sample_names=sample_names)
        formatted_files: list[FormattedFile] = self._format_sample_file_paths(moved_files)
        LOG.debug(
            f"[FORMAT SERVICE] number of formatted files: {len(formatted_files)}, number of moved files: {len(moved_files)}"
        )
        self._rename_original_files(formatted_files)
        LOG.debug(f"[FORMAT SERVICE] delivery_path: {delivery_path}")
        concatenation_map: dict[Path, Path] = self._concatenate_fastq_files(
            delivery_path=delivery_path,
            sample_names=sample_names,
        )
        self._replace_fastq_paths(
            concatenation_maps=concatenation_map,
            formatted_files=formatted_files,
        )
        return formatted_files

    @staticmethod
    def _get_sample_names(sample_files: list[SampleFile]) -> set[str]:
        """Extract sample names from the sample files."""
        return {sample_file.sample_name for sample_file in sample_files}

    def _create_sample_directories(self, sample_names: set[str], delivery_path: Path) -> None:
        """Create directories for each sample name only if the file name formatter is the NestedSampleFileFormatter.
        args:
            sample_names: set[str]: Set of sample names.
            delivery_path: Path: Path to the delivery directory.
        """
        if not isinstance(self.path_name_formatter, NestedStructurePathFormatter):
            return
        for sample_name in sample_names:
            self.file_manager.create_directories(base_path=delivery_path, directories={sample_name})

    def _format_sample_file_paths(self, sample_files: list[SampleFile]) -> list[FormattedFile]:
        """
        Return a list of formatted sample files.
        args:
            sample_files: The sample files to format
        """
        return [
            FormattedFile(
                original_path=sample_file.file_path,
                formatted_path=self.path_name_formatter.format_file_path(
                    file_path=sample_file.file_path,
                    provided_id=sample_file.sample_id,
                    provided_name=sample_file.sample_name,
                ),
            )
            for sample_file in sample_files
        ]

    def _rename_original_files(self, formatted_files: list[FormattedFile]) -> None:
        """
        Rename the formatted files.
        args:
            formatted_files: list[FormattedFile]: List of formatted files.
        """
        LOG.debug("[FORMAT SERVICE] Renaming original files")
        for formatted_file in formatted_files:
            self.file_manager.rename_file(
                src=formatted_file.original_path, dst=formatted_file.formatted_path
            )

    def _concatenate_fastq_files(
        self, delivery_path: Path, sample_names: set[str]
    ) -> dict[Path, Path]:
        """Concatenate fastq files for each sample and return the forward and reverse concatenated paths.
        args:
            delivery_path: Path: Path to the delivery directory.
            sample_names: set[str]: Set of sample names.
        returns:
            dict[Path, Path]: Dictionary with the original fastq file path as key and the concatenated path as value.
        """
        LOG.debug(f"[FORMAT SERVICE] delivery_path: {delivery_path}")
        fastq_files: list[FastqFile] = self._get_unique_sample_fastq_paths(
            sample_names=sample_names, delivery_path=delivery_path
        )
        grouped_fastq_files: dict[str, list[FastqFile]] = self._group_fastq_files_per_sample(
            sample_names=sample_names, fastq_files=fastq_files
        )
        concatenation_maps: dict[Path, Path] = {}
        for sample in grouped_fastq_files.keys():
            fastq_directory: Path = grouped_fastq_files[sample][0].fastq_file_path.parent
            forward_path: Path = generate_concatenated_fastq_delivery_path(
                fastq_directory=fastq_directory,
                sample_name=sample,
                direction=ReadDirection.FORWARD,
            )
            reverse_path: Path = generate_concatenated_fastq_delivery_path(
                fastq_directory=fastq_directory,
                sample_name=sample,
                direction=ReadDirection.REVERSE,
            )
            self.concatenation_service.concatenate(
                sample_id=sample,
                fastq_directory=fastq_directory,
                forward_output_path=forward_path,
                reverse_output_path=reverse_path,
                remove_raw=True,
            )
            concatenation_maps.update(
                self._get_concatenation_map(
                    forward_path=forward_path,
                    reverse_path=reverse_path,
                    fastq_files=grouped_fastq_files[sample],
                )
            )
        return concatenation_maps

    def _get_unique_sample_fastq_paths(
        self, sample_names: set[str], delivery_path: Path
    ) -> list[FastqFile]:
        """
        Get a list of unique sample fastq file paths given a delivery path.
        args:
            sample_names: set[str]: Set of sample names.
            delivery_path: Path: Path to the delivery directory
        returns:
            list[FastqFile]: List of FastqFile objects.
        """
        sample_paths: list[FastqFile] = []
        LOG.debug(
            f"[CONCATENATION SERVICE] Getting unique sample fastq file paths in {delivery_path}"
        )
        list_of_files: list[Path] = get_all_files_in_directory_tree(delivery_path)
        for sample_name in sample_names:
            for file in list_of_files:
                if self._has_expected_sample_name_format_match(
                    sample_name=sample_name, file_path=file
                ) and self._is_lane_fastq_file(file):
                    LOG.debug(
                        f"[CONCATENATION SERVICE] Found fastq file: {file} for sample: {sample_name}"
                    )
                    sample_paths.append(
                        FastqFile(
                            fastq_file_path=Path(delivery_path, file),
                            sample_name=sample_name,
                            read_direction=self._determine_read_direction(file),
                        )
                    )
        if not sample_paths:
            raise FileNotFoundError(
                f"Could not find any fastq files to concatenate in {delivery_path}."
            )
        return sample_paths

    @staticmethod
    def _has_expected_sample_name_format_match(sample_name: str, file_path: Path) -> bool:
        """
        Check if the sample name is an exact match in the file path.
        Fastq files are expected to have the sample name in the file path formatted as such: _{sample_name}_
        args:
            sample_name: str: The sample name to match.
            file_path: Path: The file path to check.
        """
        return f"_{sample_name}_" in file_path.as_posix()

    @staticmethod
    def _get_concatenation_map(
        forward_path: Path, reverse_path: Path, fastq_files: list[FastqFile]
    ) -> dict[Path, Path]:
        """
        Get a list of ConcatenationMap objects for a sample.
        NOTE: the fastq_files must be grouped by sample name.
        args:
            forward_path: Path: Path to the forward concatenated file.
            reverse_path: Path: Path to the reverse concatenated file.
            fastq_files: list[FastqFile]: List of fastq files for a single ample.
        """
        concatenation_map: dict[Path, Path] = {}
        for fastq_file in fastq_files:
            concatenation_map[fastq_file.fastq_file_path] = (
                forward_path if fastq_file.read_direction == ReadDirection.FORWARD else reverse_path
            )
        return concatenation_map

    @staticmethod
    def _determine_read_direction(fastq_path: Path) -> ReadDirection:
        """Determine the read direction of a fastq file.
            Assumes that the fastq file path contains 'R1' or 'R2' to determine the read direction.
        args:
            fastq_path: Path: Path to the fastq file.
        """
        if f"R{ReadDirection.FORWARD}" in fastq_path.as_posix():
            return ReadDirection.FORWARD
        return ReadDirection.REVERSE

    def _group_fastq_files_per_sample(
        self, sample_names: set[str], fastq_files: list[FastqFile]
    ) -> dict[str, list[FastqFile]]:
        """Group fastq files per sample.
        returns a dictionary with sample names as keys and a list of fastq files as values.
        args:
            sample_names: set[str]: Set of sample names.
            fastq_files: list[FastqFile]: List of fastq files.
        """

        sample_fastq_files: dict[str, list[FastqFile]] = {
            sample_name: [] for sample_name in sample_names
        }
        for fastq_file in fastq_files:
            sample_fastq_files[fastq_file.sample_name].append(fastq_file)
        self._validate_sample_fastq_file_share_same_directory(sample_fastq_files=sample_fastq_files)
        return sample_fastq_files

    def _replace_fastq_paths(
        self,
        concatenation_maps: dict[Path, Path],
        formatted_files: list[FormattedFile],
    ) -> None:
        """
        Replace the fastq file paths with the new concatenated fastq file paths.
        Uses the concatenation map with the formatted file path as key and the concatenated path as value.
        args:
            concatenation_maps: list[ConcatenationMap]: List of ConcatenationMap objects.
            formatted_files: list[FormattedFile]: List of formatted files.
        """
        for formatted_file in formatted_files:
            if self._is_lane_fastq_file(formatted_file.formatted_path):
                formatted_file.formatted_path = concatenation_maps[formatted_file.formatted_path]

    @staticmethod
    def _validate_sample_fastq_file_share_same_directory(
        sample_fastq_files: dict[str, list[FastqFile]]
    ) -> None:
        """
        Assert that all fastq files for a sample share the same directory.
        This is to ensure that the files are concatenated within the expected directory path.
        raises: ValueError if the fastq files are not in the same directory.
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

    @staticmethod
    def _is_lane_fastq_file(file_path: Path) -> bool:
        """Check if a fastq file is a from a lane and read direction.
        Note pattern: *_L[0-9]{3}_R[1-2]_[0-9]{3}.fastq.gz
        *_ is a wildcard for the flow cell id followed by sample name.
        L[0-9]{3} is the lane number, i.e. L001, L002 etc.
        R[1-2] is the read direction, i.e. R1 or R2.
        [0-9]{3} is the trailing three digits after read direction.
        args:
            file_path: Path: Path to the fastq file.
        """

        pattern = f".*_L[0-9]{{3}}_R[1-2]_[0-9]{{3}}{FileExtensions.FASTQ}{FileExtensions.GZIP}"
        return (
            re.fullmatch(
                pattern=pattern,
                string=file_path.name,
            )
            is not None
        )
