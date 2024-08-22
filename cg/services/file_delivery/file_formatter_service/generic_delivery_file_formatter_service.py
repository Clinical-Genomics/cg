import os
from pathlib import Path

from cg.constants import FileExtensions
from cg.constants.delivery import INBOX_NAME
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles, CaseFile, SampleFile
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.file_formatter_service.models import FormattedFiles, FormattedFile


class GenericDeliveryFileFormatter(DeliveryFileFormattingService):
    """
    Format the files to be delivered in the generic format.
    Expected structure:
    <customer>/inbox/<ticket_id>/<case_name>/<case_files>
    <customer>/inbox/<ticket_id>/<case_name>/<sample_name>/<sample_case_files>
    <customer>/inbox/<ticket_id>/<sample_name>/<sample_files> (i.e. fastq files)
    """

    def format_files(self, delivery_files: DeliveryFiles) -> None:
        """Format the files to be delivered in the generic format."""
        case_name: str = delivery_files.case_files[0].case_name
        samples_names: list[set[str]] = self._get_sample_names(delivery_files.sample_files)
        self._create_folder_structure(
            case_name=case_name, sample_names=samples_names, delivery_files=delivery_files
        )
        formatted_files: FormattedFiles = self._get_formatted_files(delivery_files)
        for formatted_file in formatted_files.files:
            os.rename(src=formatted_file.original_path, dst=formatted_file.formatted_path)

    @staticmethod
    def _get_sample_names(sample_files: list[SampleFile]) -> list[set[str]]:
        return [set(sample_file.sample_name for sample_file in sample_files)]

    @staticmethod
    def _is_fastq_file(file_path: Path) -> bool:
        return FileExtensions.FASTQ in str(file_path)

    @staticmethod
    def _is_inbox_path(file_path: Path):
        return INBOX_NAME in str(file_path)

    def _get_ticket_dir_path(self, file_path) -> Path:
        if self._is_inbox_path(file_path):
            return file_path.parent

    @staticmethod
    def _create_case_name_folder(ticket_path: Path, case_name: str) -> Path:
        case_dir_path = Path(ticket_path, case_name)
        case_dir_path.mkdir(exist_ok=True)
        return case_dir_path

    @staticmethod
    def _create_sample_folders(parent_path: Path, sample_names: list[str]):
        for sample_name in sample_names:
            sample_dir_path = Path(parent_path, sample_name)
            sample_dir_path.mkdir(exist_ok=True)

    def _create_folder_structure(
        self, case_name: str, sample_names: list[str], delivery_files: DeliveryFiles
    ):
        ticket_dir_path: Path = self._get_ticket_dir_path(delivery_files.sample_files[0].file_path)
        case_dir_path: Path = self._create_case_name_folder(
            ticket_path=ticket_dir_path, case_name=case_name
        )
        self._create_sample_folders(parent_path=ticket_dir_path, sample_names=sample_names)
        self._create_sample_folders(parent_path=case_dir_path, sample_names=sample_names)

    def _get_formatted_files(self, deliver_files: DeliveryFiles) -> FormattedFiles:
        formatted_case_files: list[FormattedFile] = self._format_case_files(
            deliver_files.case_files
        )
        formatted_sample_files: list[FormattedFile] = self._format_sample_files(
            sample_files=deliver_files.sample_files, case_name=deliver_files.case_files[0].case_name
        )
        return FormattedFiles(files=formatted_case_files + formatted_sample_files)

    @staticmethod
    def _format_case_files(case_files: list[CaseFile]) -> list[FormattedFile]:
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

    def _format_sample_files(
        self, sample_files: list[SampleFile], case_name: str
    ) -> list[FormattedFile]:
        formatted_files: list[FormattedFile] = []
        for sample_file in sample_files:
            replaced_sample_file_name: str = sample_file.file_path.name.replace(
                sample_file.sample_id, sample_file.sample_name
            )
            if self._is_fastq_file(sample_file.file_path):
                formatted_file_path = Path(
                    sample_file.file_path.parent, sample_file.sample_name, replaced_sample_file_name
                )
            else:
                formatted_file_path = Path(
                    sample_file.file_path.parent,
                    case_name,
                    sample_file.sample_name,
                    replaced_sample_file_name,
                )
            formatted_files.append(
                FormattedFile(
                    original_path=sample_file.file_path, formatted_path=formatted_file_path
                )
            )
        return formatted_files
