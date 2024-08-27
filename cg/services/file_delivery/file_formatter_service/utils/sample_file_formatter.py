import os
from pathlib import Path
from cg.services.file_delivery.fetch_file_service.models import SampleFile
from cg.services.file_delivery.file_formatter_service.models import FormattedFile


class SampleFileFormatter:

    def format_files(
        self, moved_files: list[SampleFile], ticket_dir_path: Path
    ) -> list[FormattedFile]:
        """Format the sample files to deliver."""
        sample_names: set[str] = self._get_sample_names(moved_files)
        self._create_sample_folders(ticket_dir_path=ticket_dir_path, sample_names=sample_names)
        return self._rename_sample_files(moved_files)

    @staticmethod
    def _get_sample_names(sample_files: list[SampleFile]) -> set[str]:
        return set(sample_file.sample_name for sample_file in sample_files)

    @staticmethod
    def _create_sample_folders(ticket_dir_path: Path, sample_names: set[str]):
        for sample_name in sample_names:
            sample_dir_path = Path(ticket_dir_path, sample_name)
            sample_dir_path.mkdir(exist_ok=True)

    @staticmethod
    def _rename_sample_files(sample_files: list[SampleFile]) -> list[FormattedFile]:
        formatted_files: list[FormattedFile] = []
        for sample_file in sample_files:
            replaced_sample_file_name: str = sample_file.file_path.name.replace(
                sample_file.sample_id, sample_file.sample_name
            )
            formatted_file_path = Path(
                sample_file.file_path.parent, sample_file.sample_name, replaced_sample_file_name
            )
            formatted_files.append(
                FormattedFile(
                    original_path=sample_file.file_path, formatted_path=formatted_file_path
                )
            )
        for formatted_file in formatted_files:
            os.rename(src=formatted_file.original_path, dst=formatted_file.formatted_path)
        return formatted_files
