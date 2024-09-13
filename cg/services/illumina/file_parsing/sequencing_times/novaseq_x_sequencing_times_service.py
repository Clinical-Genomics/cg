"""Module for the NovaSeqX sequencing times service."""

from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import ElementTree

from cg.constants.demultiplexing import RunCompletionStatusNodes
from cg.io.xml import read_xml
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.file_parsing.sequencing_times.sequencing_time_service import (
    SequencingTimesService,
)
from cg.utils.time import format_time_from_string


class NovaseqXSequencingTimesService(SequencingTimesService):
    """Class to get the sequencing times for NovaSeqX sequencing runs."""

    @staticmethod
    def get_start_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the sequencer start date and time."""
        run_completion_status_path: Path = run_directory_data.get_run_completion_status()
        tree: ElementTree = read_xml(run_completion_status_path)
        return format_time_from_string(tree.find(RunCompletionStatusNodes.RUN_START).text)

    @staticmethod
    def get_end_time(run_directory_data: IlluminaRunDirectoryData) -> datetime:
        """Get the sequencer end date and time."""
        run_completion_status_path: Path = run_directory_data.get_run_completion_status()
        tree: ElementTree = read_xml(run_completion_status_path)
        return format_time_from_string(tree.find(RunCompletionStatusNodes.RUN_END).text)
