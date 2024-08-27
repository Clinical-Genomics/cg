from pathlib import Path

from cg.constants.delivery import INBOX_NAME
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.services.file_delivery.file_formatter_service.models import FormattedFiles, FormattedFile
from cg.services.file_delivery.file_formatter_service.utils.case_file_formatter import (
    CaseFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_formatter import (
    SampleFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.utils import (
    get_ticket_dir_path,
    create_ticket_dir,
)


class ConcatenationDeliveryFileFormatter(DeliveryFileFormattingService):
    """
    Reformat the files to be delivered in the microsalt format.
    Expected structure:
    <customer>/inbox/<ticket_id>/<case_name>/<case_files>
    <customer>/inbox/<ticket_id>/<sample_name>/<sample_files>
    Extra rule:
        fastq files are concatenated into a single file per read direction.
    """

    def __init__(
        self,
        case_file_formatter: CaseFileFormatter,
        sample_file_formatter: SampleFileConcatenationFormatter,
    ):
        self.case_file_formatter = case_file_formatter
        self.sample_file_formatter = sample_file_formatter

    def format_files(self, delivery_files: DeliveryFiles) -> FormattedFiles:
        """Format the files to be delivered in the concatenated format."""
        ticket_dir_path: Path = get_ticket_dir_path(delivery_files.sample_files[0].file_path)
        create_ticket_dir(ticket_dir_path)
        formatted_files: list[FormattedFile] = []
        formatter_sample_files = self.sample_file_formatter.format_files(
            moved_files=delivery_files.sample_files,
            ticket_dir_path=ticket_dir_path,
        )
        formatted_files.extend(formatter_sample_files)
        if delivery_files.case_files:
            formatter_case_file = self.case_file_formatter.format_files(
                moved_files=delivery_files.case_files,
                ticket_dir_path=ticket_dir_path,
            )
            formatted_files.extend(formatter_case_file)
        return FormattedFiles(files=formatted_files)
