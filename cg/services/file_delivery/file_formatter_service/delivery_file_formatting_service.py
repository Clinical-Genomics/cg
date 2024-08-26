from abc import abstractmethod, ABC

from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.services.file_delivery.file_formatter_service.models import FormattedFiles
from cg.store.store import Store


class DeliveryFileFormattingService(ABC):
    """
    Abstract class that encapsulates the logic required for formatting files to deliver.
    """

    @abstractmethod
    def format_files(self, delivery_files: DeliveryFiles) -> FormattedFiles:
        """Format the files to deliver."""
        pass
