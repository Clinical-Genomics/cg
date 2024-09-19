from abc import ABC, abstractmethod

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.deliver_files.delivery_file_fetcher_service.exc import NoDeliveryFilesError

from cg.services.deliver_files.delivery_file_tag_fetcher_service.delivery_file_tag_fetcher_service import (
    FetchDeliveryFileTagsService,
)
from cg.services.deliver_files.delivery_file_fetcher_service.models import DeliveryFiles
from cg.store.store import Store


class FetchDeliveryFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for managing the files to deliver.
    1. Get a workflow and data delivery option
    2. Fetch the files based on tags from Housekeeper
    3. Return the files to deliver
    """

    @abstractmethod
    def __init__(
        self, status_db: Store, hk_api: HousekeeperAPI, tags_fetcher: FetchDeliveryFileTagsService
    ):
        self.status_db = status_db
        self.hk_api = hk_api
        self.tags_fetcher = tags_fetcher

    @abstractmethod
    def get_files_to_deliver(self, case_id: str) -> DeliveryFiles:
        """Get the files to deliver."""
        pass

    @staticmethod
    def validate_files_to_deliver(delivery_files: DeliveryFiles, case_id: str) -> DeliveryFiles:
        """Check if there are files to deliver."""
        if not delivery_files.sample_files:
            raise NoDeliveryFilesError(f"No files to deliver for case {case_id}")
        return delivery_files
