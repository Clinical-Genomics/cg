from abc import abstractmethod, ABC

from cg.services.deliver_files.delivery_file_fetcher_service.models import DeliveryFiles
from cg.services.deliver_files.delivery_file_formatter_service.models import FormattedFiles


class DeliveryFileFormattingService(ABC):
    """
    Abstract class that encapsulates the logic required for formatting files to deliver.
    """

    @abstractmethod
    def format_files(self, delivery_files: DeliveryFiles) -> FormattedFiles:
        """Format the files to deliver."""
        pass
