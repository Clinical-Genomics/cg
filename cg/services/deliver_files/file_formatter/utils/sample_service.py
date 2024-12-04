from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import SampleFile
from cg.services.deliver_files.file_formatter.models import FormattedFile
from cg.services.deliver_files.utils import FileManager


class NestedSampleFileNameFormatter:
    """
    Class to format sample file names and paths in a nested format used to deliver files to a customer inbox.
    """

    @staticmethod
    def get_sample_names(sample_files: list[SampleFile]) -> set[str]:
        """Extract sample names from the sample files."""
        return {sample_file.sample_name for sample_file in sample_files}

    @staticmethod
    def format_sample_file_names(sample_files: list[SampleFile]) -> list[FormattedFile]:
        """
        Returns formatted files with original and formatted file names:
        1. Adds a folder with sample name to the path of the sample files.
        2. Replaces sample id by sample name.
        """
        formatted_files = []
        for sample_file in sample_files:
            replaced_name = sample_file.file_path.name.replace(
                sample_file.sample_id, sample_file.sample_name
            )
            formatted_path = Path(
                sample_file.file_path.parent, sample_file.sample_name, replaced_name
            )
            formatted_files.append(
                FormattedFile(original_path=sample_file.file_path, formatted_path=formatted_path)
            )
        return formatted_files


class FlatSampleFileNameFormatter:
    """
    Class to format sample file names in place.
    """

    @staticmethod
    def get_sample_names(sample_files: list[SampleFile]) -> set[str]:
        """Extract sample names from the sample files."""
        return {sample_file.sample_name for sample_file in sample_files}

    @staticmethod
    def format_sample_file_names(sample_files: list[SampleFile]) -> list[FormattedFile]:
        """
        Returns formatted files with original and formatted file names:
        Replaces sample id by sample name.
        """
        formatted_files = []
        for sample_file in sample_files:
            replaced_name = sample_file.file_path.name.replace(
                sample_file.sample_id, sample_file.sample_name
            )
            formatted_path = Path(sample_file.file_path.parent, replaced_name)
            formatted_files.append(
                FormattedFile(original_path=sample_file.file_path, formatted_path=formatted_path)
            )
        return formatted_files


class SampleFileFormatter:
    """
    Format the sample files to deliver.
    Used for all workflows except Microsalt and Mutant.
    """

    def __init__(
        self,
        file_manager: FileManager,
        file_name_formatter: NestedSampleFileNameFormatter | FlatSampleFileNameFormatter,
    ):
        self.file_manager = file_manager
        self.file_name_formatter = file_name_formatter

    def format_files(
        self, moved_files: list[SampleFile], delivery_path: Path
    ) -> list[FormattedFile]:
        """Format the sample files to deliver and return the formatted files."""
        sample_names: set[str] = self.file_name_formatter.get_sample_names(sample_files=moved_files)
        for sample_name in sample_names:
            self.file_manager.create_directories(base_path=delivery_path, directories={sample_name})
        formatted_files: list[FormattedFile] = self.file_name_formatter.format_sample_file_names(
            sample_files=moved_files
        )
        for formatted_file in formatted_files:
            self.file_manager.rename_file(
                src=formatted_file.original_path, dst=formatted_file.formatted_path
            )
        return formatted_files
