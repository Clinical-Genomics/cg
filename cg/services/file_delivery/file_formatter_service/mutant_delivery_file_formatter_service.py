from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.services.file_delivery.file_formatter_service.delivery_file_formatting_service import (
    DeliveryFileFormattingService,
)


class MutantDeliveryFileFormatter(DeliveryFileFormattingService):
    """
    Reformat the files to be delivered in the mutant format.

    """

    def format_files(self, delivery_files: DeliveryFiles) -> None:
        """Format the files to be delivered in the generic format."""
