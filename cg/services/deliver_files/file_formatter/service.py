import logging
import os
from pathlib import Path

from cg.constants.delivery import INBOX_NAME
from cg.services.deliver_files.file_fetcher.models import (
    CaseFile,
    DeliveryFiles,
    SampleFile,
)
from cg.services.deliver_files.file_formatter.abstract import (
    DeliveryFileFormattingService,
)
from cg.services.deliver_files.file_formatter.models import (
    FormattedFile,
    FormattedFiles,
)
from cg.services.deliver_files.file_formatter.utils.case_service import (
    CaseFileFormatter,
)
from cg.services.deliver_files.file_formatter.utils.sample_concatenation_service import (
    SampleFileConcatenationFormatter,
)
from cg.services.deliver_files.file_formatter.utils.sample_service import (
    SampleFileFormatter,
)

LOG = logging.getLogger(__name__)


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
        LOG.debug("[FORMAT SERVICE] Formatting files for delivery")
        ticket_dir_path: Path = delivery_files.delivery_data.customer_ticket_inbox
        self._create_ticket_dir(ticket_dir_path)
        formatted_files: list[FormattedFile] = self._format_sample_and_case_files(
            sample_files=delivery_files.sample_files,
            case_files=delivery_files.case_files,
            ticket_dir_path=ticket_dir_path,
        )
        return FormattedFiles(files=formatted_files)

    def _format_sample_and_case_files(
        self, sample_files: list[SampleFile], case_files: list[CaseFile], ticket_dir_path: Path
    ) -> list[FormattedFile]:
        """Helper method to format both sample and case files."""
        formatted_files: list[FormattedFile] = self.sample_file_formatter.format_files(
            moved_files=sample_files,
            ticket_dir_path=ticket_dir_path,
        )
        if case_files:
            formatted_case_files: list[FormattedFile] = self.case_file_formatter.format_files(
                moved_files=case_files,
                ticket_dir_path=ticket_dir_path,
            )
            formatted_files.extend(formatted_case_files)
        return formatted_files

    @staticmethod
    def _create_ticket_dir(ticket_dir_path: Path) -> None:
        """Create the ticket directory if it does not exist."""
        os.makedirs(ticket_dir_path, exist_ok=True)
