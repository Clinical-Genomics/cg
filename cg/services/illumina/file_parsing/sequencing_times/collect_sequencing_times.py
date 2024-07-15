"""Class to collect sequencing times for Illumina sequencing runs."""

from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData

from cg.services.illumina.file_parsing.sequencing_times.sequencing_times_service import (
    SequencingTimesService,
)


class CollectSequencingTimes:
    """Class to collect sequencing times for Illumina sequencing runs."""

    def __init__(self, time_service: SequencingTimesService):
        """Initialize the class."""
        self.time_service = time_service

    def get_end_time(self, run_directory_data: IlluminaRunDirectoryData):
        """Get the end time of the sequencing run."""
        return self.time_service.get_end_time(run_directory_data)

    def get_start_time(self, run_directory_data: IlluminaRunDirectoryData):
        """Get the start time of the sequencing run."""
        return self.time_service.get_start_time(run_directory_data)
