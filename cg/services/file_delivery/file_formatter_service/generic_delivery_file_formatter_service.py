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
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.utils import (
    get_ticket_dir_path,
    create_ticket_dir,
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
        """Format the files to be delivered and return the formatted files in the generic format."""
        ticket_dir_path: Path = get_ticket_dir_path(delivery_files.sample_files[0].file_path)
        create_ticket_dir(ticket_dir_path)
        formatted_files: list[FormattedFile] = []
        formatted_sample_files: list[FormattedFile] = self.sample_file_formatter.format_files(
            moved_files=delivery_files.sample_files,
            ticket_dir_path=get_ticket_dir_path(delivery_files.sample_files[0].file_path),
        )
        formatted_files.extend(formatted_sample_files)
        if delivery_files.case_files:
            formatted_case_file: list[FormattedFile] = self.case_file_formatter.format_files(
                moved_files=delivery_files.case_files,
                ticket_dir_path=get_ticket_dir_path(delivery_files.case_files[0].file_path),
            )
            formatted_files.extend(formatted_case_file)
        return FormattedFiles(files=formatted_files)
