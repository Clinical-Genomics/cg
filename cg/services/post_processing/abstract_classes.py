"""Post-processing service abstract classes."""

from abc import ABC, abstractmethod
from pathlib import Path

from cg.services.post_processing.abstract_models import PostProcessingDTOs, RunData, RunMetrics


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

    @abstractmethod
    def store_post_processing_data(self, run_data: RunData, dry_run: bool = False):
        pass


class PostProcessingHKService(ABC):
    """Abstract class that manages storing of files for an instrument run."""

    @abstractmethod
    def store_files_in_housekeeper(self, run_data: RunData, dry_run: bool = False):
        pass


class PostProcessingService(ABC):
    """Abstract class that encapsulates the logic required for post-processing a sequencing run."""

    @abstractmethod
    def post_process(self, run_name: str, dry_run: bool = False):
        """Store sequencing metrics in statusdb and relevant files in housekeeper"""
        pass
