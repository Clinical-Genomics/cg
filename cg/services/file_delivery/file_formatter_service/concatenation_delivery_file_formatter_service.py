from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.services.file_delivery.file_formatter_service.case_file_formatter import CaseFileFormatter
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)
from cg.services.file_delivery.file_formatter_service.sample_concatenation_file_formatter import (
    SampleConcatenationFileFormatter,
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
        sample_file_formatter: SampleConcatenationFileFormatter,
        concatenation_service: FastqConcatenationService,
    ):
        self.case_file_formatter = case_file_formatter
        self.sample_file_formatter = sample_file_formatter
        self.concatenation_service = concatenation_service

    def format_files(self, delivery_files: DeliveryFiles) -> None:
        """Format the files to be delivered in the generic format."""
