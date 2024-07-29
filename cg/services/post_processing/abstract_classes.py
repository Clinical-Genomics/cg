"""Post-processing service abstract classes."""

from abc import ABC, abstractmethod
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.post_processing.abstract_models import PostProcessingDTOs, RunData, RunMetrics
from cg.store.store import Store


class RunDataGenerator(ABC):
    """Abstract class for that holds functionality to create a run data model."""

    @abstractmethod
    def get_run_data(self, run_name: str, sequencing_dir: str) -> RunData:
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
    """Abstract class that manages the metrics parsing related to an instrument run."""

    @abstractmethod
    def parse_metrics(self, run_data: RunData) -> RunMetrics:
        pass


class PostProcessingDataTransferService(ABC):
    """Abstract class that manages the data transfer from parsed metrics to the database structure."""

    @abstractmethod
    def get_post_processing_dtos(self, run_data: RunData) -> PostProcessingDTOs:
        pass


class PostProcessingStoreService(ABC):
    """Abstract class that manages storing data transfer objects in the database."""

    def store_post_processing_data(self, run_data: RunData):
        pass


class PostProcessingHKService(ABC):
    """Abstract class that manages storing of files for an instrument run."""

    def store_files_in_housekeeper(self, run_data: RunData):
        pass


class PostProcessingService(ABC):
    """Abstract class that encapsulates the logic required for post-processing and instrument run."""

    @abstractmethod
    def post_process(self, run_name):
        """Store sequencing metrics in statusdb and relevant files in housekeeper"""
        pass
