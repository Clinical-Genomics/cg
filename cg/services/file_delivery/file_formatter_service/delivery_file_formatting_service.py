from abc import abstractmethod, ABC

from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.store.store import Store


class DeliveryFileFormattingService(ABC):
    """
    Abstract class that encapsulates the logic required for formatting files to deliver.
    """

    @abstractmethod
    def format_files(self, delivery_files: DeliveryFiles) -> None:
        """Format the files to deliver."""
        pass
