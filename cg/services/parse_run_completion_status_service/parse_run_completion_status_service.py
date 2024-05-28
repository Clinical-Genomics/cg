"""Service to parse the RunInfo.xml file."""

from cg.constants.demultiplexing import RunCompletionStatusNodes
from cg.io.xml import read_xml
from cg.utils.time import format_time_from_string
from datetime import datetime
from pathlib import Path
from xml.etree.ElementTree import ElementTree


class ParseRunCompletionStatusService:

    @staticmethod
    def _parse_run_completion_status_path(run_completion_status_path: Path) -> ElementTree:
        """Parse the RunInfo.xml file."""
        return read_xml(file_path=run_completion_status_path)

    def get_start_time(self, run_completion_status_path: Path) -> datetime:
        """Get the sequencer start date and time."""
        tree: ElementTree = self._parse_run_completion_status_path(run_completion_status_path)
        return format_time_from_string(tree.find(RunCompletionStatusNodes.RUN_START).text)

    def get_end_time(self, run_completion_status_path: Path) -> datetime:
        """Get the sequencer end date and time."""
        tree: ElementTree = self._parse_run_completion_status_path(run_completion_status_path)
        return format_time_from_string(tree.find(RunCompletionStatusNodes.RUN_END).text)
