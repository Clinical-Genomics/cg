"""Module for the HiSeq2500 sequencing times service."""

from datetime import datetime

from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.file_parsing.sequencing_times.sequencing_time_service import (
    SequencingTimesService,
)


class Hiseq2500SequencingTimesService(SequencingTimesService):
    """Class to get the sequencing times for HiSeq2500 sequencing runs."""

    @staticmethod
    def get_start_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the sequencer start date and time."""
        return run_directory_data.sequenced_at

    @staticmethod
    def get_end_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the sequencer end date and time."""
        return run_directory_data.sequenced_at
