"""Module for the HiSeqX sequencing times service."""

from datetime import datetime
from pathlib import Path

from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.file_parsing.sequencing_times.sequencing_time_service import (
    SequencingTimesService,
)
from cg.utils.files import get_source_modified_time_stamp
from cg.utils.time import format_time_from_ctime


class HiseqXSequencingTimesService(SequencingTimesService):
    """Class to get the sequencing times for HiSeqX sequencing runs."""

    @staticmethod
    def get_start_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the start time of the sequencing run."""
        return run_directory_data.sequenced_at

    @staticmethod
    def get_end_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the end time of the sequencing run."""
        file_path: Path = run_directory_data.get_sequencing_completed_path
        modified_time: float = get_source_modified_time_stamp(file_path)
        return format_time_from_ctime(modified_time)
