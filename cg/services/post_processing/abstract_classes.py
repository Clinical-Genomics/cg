"""Post-processing service abstract classes."""

from abc import abstractmethod, ABC
from pathlib import Path

from pydantic import BaseModel

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.post_processing.abstract_models import PostProcessingDTOs, RunMetrics, RunData
from cg.store.store import Store


class RunDataGenerator(ABC):
    """Abstract class for that holds functionality to create a run data model."""

    @abstractmethod
    def _validate_run_path(self) -> None:
        pass

    @abstractmethod
    def get_run_data(self) -> RunData:
        pass


class RunFileManager(ABC):
    """Abstract class that manages files related to an instrument run."""

    @abstractmethod
    def get_files_to_parse(self, run_data: RunData) -> list[Path]:
        """Get the files required for the PostProcessingMetricsService."""
        pass

    @abstractmethod
    def get_files_to_store(self, run_data: RunData) -> list[Path]:
        """Get the files to store for the PostProcessingHKService."""
        pass


class PostProcessingMetricsParser(ABC):

    @abstractmethod
    def parse_metrics(self, metrics_paths: list[Path]) -> RunMetrics:
        pass


class PostProcessingDataTransferService(ABC):
    def __init__(self, metrics_service: PostProcessingMetricsParser, file_manager: RunFileManager):
        self.metrics_service = metrics_service
        self.file_manager = file_manager

    def get_post_processing_dtos(self) -> PostProcessingDTOs:
        pass


class PostProcessingStoreService(ABC):
    def __init__(self, store: Store, data_transfer_service: PostProcessingDataTransferService):
        self.store: Store = store
        self.data_transfer_service: PostProcessingDataTransferService = data_transfer_service

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

    def store_files_in_housekeeper(self, file_to_store: list[Path]):
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
        pass
