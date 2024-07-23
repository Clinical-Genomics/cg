"""Post-processing service abstract classes."""

from abc import abstractmethod, ABC
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.store.store import Store


class RunDirectoryData(ABC):
    """Abstract class for that holds information from the run directory."""

    pass


class RunFileManager(ABC):
    """Abstract class that manages files related to an instrument run."""

    pass


class PostProcessingMetricsService(ABC):

    @abstractmethod
    def parse_metrics(self, metrics_dir: Path):
        pass


class PostProcessingDataTransferService(ABC):
    def __init__(self, metrics_service: PostProcessingMetricsService):
        self.metrics_service = metrics_service

    def create_run_device_dto(self, run_name):
        pass

    def create_instrument_run_dto(self, run_name):
        pass

    def create_sample_run_dto(self, run_name, sample_id):
        pass


class PostProcessingStoreService(ABC):
    def __init__(self, store: Store, data_transfer_service: PostProcessingDataTransferService):
        self.store: Store = store
        self.data_transfer_service: PostProcessingDataTransferService = data_transfer_service

    def _get_sample_ids(self, run_name):
        pass

    def _create_run_device(self, run_name):
        pass

    def _create_instrument_run(self, run_name):
        pass

    def _create_sample_run_metrics(self, run_name):
        pass

    def store_post_processing_data(self, run_name):
        pass


class PostProcessingHKService(ABC):
    def __init__(self, hk_api: HousekeeperAPI):
        self.hk_api = HousekeeperAPI

    def _get_files_to_store(self):
        pass

    def store_files_in_housekeeper(self, run_name):
        pass


class PostProcessingService(ABC):

    def __init(
        self, store_service: PostProcessingStoreService, hk_service: PostProcessingHKService
    ):
        self.store_service = store_service
        self.hk_service = hk_service

    @abstractmethod
    def post_process(self, run_name):
        """Store sequencing metrics in statusdb and relevant files in housekeeper"""
        self.store_service.store_post_processing_data(run_name)
        self.hk_service.store_files_in_housekeeper(run_name)
