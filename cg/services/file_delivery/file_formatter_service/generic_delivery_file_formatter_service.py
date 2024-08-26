import os
from pathlib import Path
from cg.constants.delivery import INBOX_NAME
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.services.file_delivery.file_formatter_service.case_file_formatter import CaseFileFormatter
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.file_formatter_service.models import FormattedFiles, FormattedFile
from cg.services.file_delivery.file_formatter_service.sample_file_formatter import (
    SampleFileFormatter,
)


class GenericDeliveryFileFormatter(DeliveryFileFormattingService):
    """
    Format the files to be delivered in the generic format.
    Expected structure:
    <customer>/inbox/<ticket_id>/<case_name>/<case_files>
    <customer>/inbox/<ticket_id>/<sample_name>/<sample_files>
    """

    def __init__(
        self, case_file_formatter: CaseFileFormatter, sample_file_formatter: SampleFileFormatter
    ):
        self.case_file_formatter = case_file_formatter
        self.sample_file_formatter = sample_file_formatter

    def format_files(self, delivery_files: DeliveryFiles) -> FormattedFiles:
        """Format the files to be delivered in the generic format."""
        formatted_files: FormattedFiles = self._get_files_to_format(delivery_files)
        for formatted_file in formatted_files.files:
            os.rename(src=formatted_file.original_path, dst=formatted_file.formatted_path)
        return formatted_files

    @staticmethod
    def _is_inbox_path(file_path: Path):
        return INBOX_NAME in str(file_path)

    def _get_ticket_dir_path(self, file_path) -> Path:
        if self._is_inbox_path(file_path):
            return file_path.parent

    def _get_files_to_format(self, delivery_files: DeliveryFiles):
        formatted_files: list[FormattedFile] = []
        if delivery_files.case_files:
            formatter_case_file = self.case_file_formatter.format_case_files(
                case_files=delivery_files.case_files,
                ticket_dir_path=self._get_ticket_dir_path(delivery_files.case_files[0].file_path),
            )
            formatted_files.extend(formatter_case_file)
        formatter_sample_files = self.sample_file_formatter.format_sample_files(
            sample_files=delivery_files.sample_files,
            ticket_dir_path=self._get_ticket_dir_path(delivery_files.sample_files[0].file_path),
        )
        formatted_files.extend(formatter_sample_files)
        return FormattedFiles(files=formatted_files)
