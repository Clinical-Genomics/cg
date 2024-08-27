from pathlib import Path
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.services.file_delivery.file_formatter_service.generic_delivery_file_formatter_service import (
    GenericDeliveryFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.models import FormattedFiles, FormattedFile
from cg.services.file_delivery.file_formatter_service.utils.case_file_formatter import (
    CaseFileFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.sample_file_concatenation_formatter import (
    SampleFileConcatenationFormatter,
)
from cg.services.file_delivery.file_formatter_service.utils.utils import (
    get_ticket_dir_path,
    create_ticket_dir,
)


class ConcatenationDeliveryFileFormatter(GenericDeliveryFileFormatter):
    """
    Reformat the files to be delivered and concatenate fastq files.
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
        super().__init__(
            case_file_formatter=case_file_formatter, sample_file_formatter=sample_file_formatter
        )
