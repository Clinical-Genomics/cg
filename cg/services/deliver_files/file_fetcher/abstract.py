import logging
from abc import ABC, abstractmethod

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.deliver_files.file_fetcher.exc import NoDeliveryFilesError
from cg.services.deliver_files.file_fetcher.models import DeliveryFiles
from cg.services.deliver_files.tag_fetcher.abstract import (
    FetchDeliveryFileTagsService,
)
from cg.store.store import Store

LOG = logging.getLogger(__name__)


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
