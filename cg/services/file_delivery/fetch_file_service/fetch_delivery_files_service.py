from abc import ABC, abstractmethod

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.services.file_delivery.fetch_file_service.models import DeliveryFiles
from cg.store.store import Store


class FetchDeliveryFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for managing the files to deliver.
    1. Get a workflow and data delivery option
    2. Fetch the files based on tags from Housekeeper
    3. Return the files to deliver
    """

    @abstractmethod
    def __init__(self, status_db: Store, hk_api: HousekeeperAPI):
        self.status_db = status_db
        self.hk_api = hk_api

    @abstractmethod
    def get_files_to_deliver(self, case_id: str) -> DeliveryFiles:
        """Get the files to deliver."""
        pass

    @staticmethod
    def get_analysis_sample_tags_for_workflow(workflow: Workflow) -> list[set[str]]:
        return PIPELINE_ANALYSIS_TAG_MAP[workflow]["sample_tags"]

    @staticmethod
    def get_analysis_case_tags_for_workflow(workflow: Workflow) -> list[set[str]]:
        return PIPELINE_ANALYSIS_TAG_MAP[workflow]["case_tags"]
