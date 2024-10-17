from abc import abstractmethod, ABC

from cg.services.deliver_files.file_fetcher.models import DeliveryFiles


class FilterDeliveryFilesService(ABC):

    @abstractmethod
    def filter_delivery_files(self, delivery_files: DeliveryFiles, sample_id: str) -> DeliveryFiles:
        pass
