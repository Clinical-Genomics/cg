import logging
from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import SampleFile
from cg.services.deliver_files.file_formatter.files.abstract import FileFormatter
from cg.services.deliver_files.file_formatter.destination.models import FormattedFile
from cg.services.deliver_files.file_formatter.path_name.abstract import PathNameFormatter
from cg.services.deliver_files.utils import FileManager

LOG = logging.getLogger(__name__)


class SampleFileFormatter(FileFormatter):
    """
    Format the sample files to deliver.
    Used for all workflows except Microsalt and Mutant.
    args:
        file_manager: The file manager
        path_name_formatter: The path name formatter to format paths to either a flat or nested structure in the delivery destination
    """

    def __init__(
        self,
        file_manager: FileManager,
        path_name_formatter: PathNameFormatter,
    ):
        self.file_manager = file_manager
        self.path_name_formatter = path_name_formatter

    def format_files(
        self, moved_files: list[SampleFile], delivery_path: Path
    ) -> list[FormattedFile]:
        """
        Format the sample files to deliver and return the formatted files.
        args:
            moved_sample_files: The sample files to format. These are files that have been moved from housekeeper to the delivery path.
            delivery_path: The path to deliver the files to
        """
        LOG.debug("[FORMAT SERVICE] Formatting sample files")
        sample_names: set[str] = self._get_sample_names(sample_files=moved_files)
        for sample_name in sample_names:
            self.file_manager.create_directories(base_path=delivery_path, directories={sample_name})
        formatted_files: list[FormattedFile] = self._format_sample_file_paths(moved_files)
        for formatted_file in formatted_files:
            self.file_manager.rename_file(
                src=formatted_file.original_path, dst=formatted_file.formatted_path
            )
        return formatted_files

    @staticmethod
    def _get_sample_names(sample_files: list[SampleFile]) -> set[str]:
        """Extract sample names from the sample files."""
        return {sample_file.sample_name for sample_file in sample_files}

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
