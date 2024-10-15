from abc import abstractmethod, ABC

from cg.services.deliver_files.tag_fetcher.models import DeliveryFileTags


class FetchDeliveryFileTagsService(ABC):
    """
    Abstract class that encapsulates the logic required for fetching tags for files to deliver.
    """

    @abstractmethod
    def fetch_tags(self, workflow: str) -> DeliveryFileTags:
        """Fetch the tags for the files to deliver."""
        pass
