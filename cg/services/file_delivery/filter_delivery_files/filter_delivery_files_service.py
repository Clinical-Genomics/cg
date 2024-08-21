from abc import abstractmethod, ABC

from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles


class FilterDeliveryFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for filtering files to deliver.
    """

    @abstractmethod
    def filter_files(self, deliver_files: DeliveryFiles) -> None:
        """Filter the files to deliver."""
        pass
