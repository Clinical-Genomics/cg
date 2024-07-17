"""Module for the hiseq sequencers sequencing times service."""

from datetime import datetime

from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


class HiseqSequencingTimesService:

    @staticmethod
    def get_end_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the end time of the sequencing run."""
        return run_directory_data.sequenced_at

    @staticmethod
    def get_start_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the start time of the sequencing run."""
        return run_directory_data.sequenced_at
