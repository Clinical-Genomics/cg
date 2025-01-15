from abc import ABC, abstractmethod
from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import DeliveryFiles


class DestinationFilesMover(ABC):
    @abstractmethod
    def move_files(self, delivery_files: DeliveryFiles, delivery_base_path: Path) -> DeliveryFiles:
        """Move files to the delivery folder."""
        pass
