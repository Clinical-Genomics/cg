import os
from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import CaseFile
from cg.services.deliver_files.file_formatter.models import FormattedFile


class CaseFileFormatter:

    def format_files(
        self, moved_files: list[CaseFile], ticket_dir_path: Path
    ) -> list[FormattedFile]:
        """Format the case files to deliver and return the formatted files."""
        self._create_case_name_folder(
            ticket_path=ticket_dir_path, case_name=moved_files[0].case_name
        )
        return self._format_case_files(moved_files)

    def _format_case_files(self, case_files: list[CaseFile]) -> list[FormattedFile]:
        formatted_files: list[FormattedFile] = self._get_formatted_files(case_files)
        for formatted_file in formatted_files:
            os.rename(src=formatted_file.original_path, dst=formatted_file.formatted_path)
        return formatted_files

    @staticmethod
    def _create_case_name_folder(ticket_path: Path, case_name: str) -> None:
        case_dir_path = Path(ticket_path, case_name)
        case_dir_path.mkdir(exist_ok=True)

    @staticmethod
    def _get_formatted_files(case_files: list[CaseFile]) -> list[FormattedFile]:
        """
        Returns formatted files:
        1. Adds a folder with case name to the path of the case files.
        2. Replaces case id by case name.
        """
        formatted_files: list[FormattedFile] = []
        for case_file in case_files:
            replaced_case_file_name: str = case_file.file_path.name.replace(
                case_file.case_id, case_file.case_name
            )
            formatted_file_path = Path(
                case_file.file_path.parent, case_file.case_name, replaced_case_file_name
            )
            formatted_files.append(
                FormattedFile(original_path=case_file.file_path, formatted_path=formatted_file_path)
            )
        return formatted_files
