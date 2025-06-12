"""Post-processing service abstract classes."""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

from cg.services.run_devices.abstract_models import PostProcessingDTOs, RunData, RunMetrics
from cg.services.run_devices.constants import POST_PROCESSING_COMPLETED

LOG = logging.getLogger(__name__)


class RunDataGenerator(ABC):
    """Abstract class that holds functionality to create a run data object."""

    @abstractmethod
    def get_run_data(self, run_name: str, sequencing_dir: str) -> RunData:
        """Get the run data for a sequencing run."""
        pass


class RunValidator(ABC):
    """Abstract class that holds functionality to validate a run and ensure it can start post processing."""

    @abstractmethod
    def ensure_post_processing_can_start(self, run_data: RunData):
        """Ensure a post processing run can start."""
        pass

    @abstractmethod
    def validate_run_files(self, run_data: RunData):
        """Validate presence run files."""
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
        """Parse the sequencing run metrics."""
        pass


class PostProcessingDataTransferService(ABC):
    """Abstract class that manages data transfer from parsed metrics to the database structure."""

    @abstractmethod
    def get_post_processing_dtos(self, run_data: RunData) -> PostProcessingDTOs:
        """Get the data transfer objects for the PostProcessingStoreService."""
        pass


class PostProcessingStoreService(ABC):
    """Abstract class that manages storing data transfer objects in the database."""

    @abstractmethod
    def store_post_processing_data(self, run_data: RunData, dry_run: bool = False):
        """Store the data transfer objects in the database."""
        pass


class PostProcessingHKService(ABC):
    """Abstract class that manages storing of files for an instrument run."""

    @abstractmethod
    def store_files_in_housekeeper(self, run_data: RunData, dry_run: bool = False):
        """Store the files in Housekeeper."""
        pass


class PostProcessingService(ABC):
    """Abstract class that encapsulates the logic required for post-processing a sequencing run."""

    @abstractmethod
    def post_process(self, run_name: str, dry_run: bool = False):
        """Store sequencing metrics in StatusDB and relevant files in Housekeeper."""
        pass

    @abstractmethod
    def is_run_processed(self, run_name: str) -> bool:
        """Check if a run has been post-processed."""
        pass

    @abstractmethod
    def can_post_processing_start(self, run_name: str) -> bool:
        """Check if a run can be post processed."""
        pass

    @staticmethod
    def _touch_post_processing_complete(run_data: RunData, dry_run: bool = False) -> None:
        """Touch the post-processing complete file."""
        processing_complete_file = Path(run_data.full_path, POST_PROCESSING_COMPLETED)
        if not dry_run:
            processing_complete_file.touch()
        LOG.debug(f"Post-processing complete for {run_data.full_path}")
