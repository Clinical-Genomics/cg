"""Module to get the sequencing completed service."""

from datetime import datetime
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


class HiseqGASequencingTimesService:
    """Class to get the modified time of the SequenceComplete.txt for novaseq 6000 sequencing runs."""

    @staticmethod
    def get_end_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the sequencer end date and time."""
        return run_directory_data.sequenced_at

    @staticmethod
    def get_start_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the sequencer start date and time."""
        return run_directory_data.sequenced_at
