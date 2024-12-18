import logging
from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import CaseFile
from cg.services.deliver_files.file_formatter.files.abstract import FileFormatter
from cg.services.deliver_files.file_formatter.destination.models import FormattedFile
from cg.services.deliver_files.file_formatter.path_name.abstract import PathNameFormatter
from cg.services.deliver_files.file_formatter.path_name.nested_structure import (
    NestedStructurePathFormatter,
)
from cg.services.deliver_files.utils import FileManager

LOG = logging.getLogger(__name__)


class CaseFileFormatter(FileFormatter):
    """
    Format the case files to deliver and return the formatted files.
    args:
        path_name_formatter: The path name formatter to format paths to either a flat or nested structure in the delivery destination
        file_manager: The file manager
    """

    def __init__(
        self,
        path_name_formatter: PathNameFormatter,
        file_manager: FileManager,
    ):
        self.path_name_formatter = path_name_formatter
        self.file_manager = file_manager

    def format_files(self, moved_files: list[CaseFile], delivery_path: Path) -> list[FormattedFile]:
        """Format the case files to deliver and return the formatted files.
        args:
            moved_files: The case files to format
            delivery_path: The path to deliver the files to
        """
        LOG.debug("[FORMAT SERVICE] Formatting case files")
        self._create_case_name_folder(
            delivery_path=delivery_path, case_name=moved_files[0].case_name
        )
        return self._format_case_files(moved_files)

    def _format_case_files(self, case_files: list[CaseFile]) -> list[FormattedFile]:
        """Format the case files to deliver and return the formatted files.
        args:
            case_files: The case files to format
        """
        formatted_files: list[FormattedFile] = self._get_formatted_paths(case_files)
        for formatted_file in formatted_files:
            self.file_manager.rename_file(
                src=formatted_file.original_path, dst=formatted_file.formatted_path
            )
        return formatted_files

    def _create_case_name_folder(self, delivery_path: Path, case_name: str) -> None:
        """
        Create a folder for the case in the delivery path.
        The folder is only created if the provided PathStructureFormatter is a NestedStructurePathFormatter.
        args:
            delivery_path: The path to deliver the files to
            case_name: The name of the case
        """
        LOG.debug(f"[FORMAT SERVICE] Creating folder for case: {case_name}")
        if isinstance(self.path_name_formatter, NestedStructurePathFormatter):
            self.file_manager.create_directories(base_path=delivery_path, directories={case_name})

    def _get_formatted_paths(self, case_files: list[CaseFile]) -> list[FormattedFile]:
        """Return a list of formatted case files.
        args:
            case_files: The case files to format
        """
        formatted_files: list[FormattedFile] = []
        for case_file in case_files:
            formatted_path = self.path_name_formatter.format_file_path(
                file_path=case_file.file_path,
                provided_id=case_file.case_id,
                provided_name=case_file.case_name,
            )
            formatted_files.append(
                FormattedFile(original_path=case_file.file_path, formatted_path=formatted_path)
            )
        return formatted_files
