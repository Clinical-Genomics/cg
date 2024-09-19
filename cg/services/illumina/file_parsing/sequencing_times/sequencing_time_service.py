"""Abstract class for the sequencing times service."""

from abc import ABC, abstractmethod
from datetime import datetime

from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


class SequencingTimesService(ABC):
    """Abstract class for the sequencing times service."""

    @abstractmethod
    def get_start_time(self, run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the start time of the sequencing run."""
        pass

    @abstractmethod
    def get_end_time(self, run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the end time of the sequencing run."""
        pass
