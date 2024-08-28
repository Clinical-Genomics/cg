import os
from pathlib import Path
from cg.constants.delivery import INBOX_NAME
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.services.file_delivery.file_formatter_service.utils.case_file_formatter import (
    CaseFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.file_formatter_service.models import FormattedFiles, FormattedFile
from cg.services.file_delivery.file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)


class DeliveryFileFormatter(DeliveryFileFormattingService):
    """
    Format the files to be delivered in the generic format.
    Expected structure:
    <customer>/inbox/<ticket_id>/<case_name>/<case_files>
    <customer>/inbox/<ticket_id>/<sample_name>/<sample_files>
    """

    def __init__(
        self,
        case_file_formatter: CaseFileFormatter,
        sample_file_formatter: SampleFileFormatter | SampleFileConcatenationFormatter,
    ):
        self.case_file_formatter = case_file_formatter
        self.sample_file_formatter = sample_file_formatter

    def format_files(self, delivery_files: DeliveryFiles) -> FormattedFiles:
        """Format the files to be delivered and return the formatted files in the generic format."""
        ticket_dir_path: Path = self.get_folder_under_inbox(
            delivery_files.sample_files[0].file_path
        )
        self._create_ticket_dir(ticket_dir_path)
        formatted_files = self._format_sample_and_case_files(
            sample_files=delivery_files.sample_files,
            case_files=delivery_files.case_files,
            ticket_dir_path=ticket_dir_path,
        )
        return FormattedFiles(files=formatted_files)

    def _format_sample_and_case_files(
        self, sample_files, case_files, ticket_dir_path
    ) -> list[FormattedFile]:
        """Helper method to format both sample and case files."""
        formatted_files = self.sample_file_formatter.format_files(
            moved_files=sample_files,
            ticket_dir_path=ticket_dir_path,
        )
        if case_files:
            formatted_case_files = self.case_file_formatter.format_files(
                moved_files=case_files,
                ticket_dir_path=ticket_dir_path,
            )
            formatted_files.extend(formatted_case_files)
        return formatted_files

    @staticmethod
    def get_folder_under_inbox(file_path: Path) -> Path:
        try:
            inbox_index = file_path.parts.index(INBOX_NAME)
            return Path(*file_path.parts[: inbox_index + 2])
        except ValueError:
            raise ValueError(f"Could not find the inbox directory in the path: {file_path}")

    @staticmethod
    def _create_ticket_dir(ticket_dir_path: Path) -> None:
        os.makedirs(ticket_dir_path, exist_ok=True)
