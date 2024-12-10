from abc import abstractmethod, ABC
from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.file_formatter.destination.models import FormattedFiles


class ComponentFormatter(ABC):

    @abstractmethod
    def format_files(self, moved_files: DeliveryFiles, delivery_path: Path) -> FormattedFiles:
        """Format the files to deliver."""
        pass
