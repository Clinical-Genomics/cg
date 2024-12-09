from abc import abstractmethod, ABC
from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.file_formatter.models import FormattedFiles


class DeliveryFileFormattingService(ABC):
    """
    Abstract class that encapsulates the logic required for formatting files to deliver.
    """

    @abstractmethod
    def format_files(self, delivery_files: DeliveryFiles, delivery_path: Path) -> FormattedFiles:
        """Format the files to deliver."""
        pass
