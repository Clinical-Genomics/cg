"""Service to parse the RunInfo.xml file."""

import re
from pathlib import Path

from xml.etree.ElementTree import ElementTree

from cg.constants.demultiplexing import RunCompletionStatusNodes
from cg.io.xml import read_xml
from datetime import datetime

DATE_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class ParseRunCompletionStatusService:

    @classmethod
    def format_time(cls, time: str) -> datetime:
        """Format the time."""
        no_microseconds: str = re.sub(r"\.\d+", "", time)
        no_microseconds_no_time_zone = re.sub(r"[+-]\d{2}:\d{2}$", "", no_microseconds)
        return datetime.strptime(no_microseconds_no_time_zone, DATE_TIME_FORMAT)

    @staticmethod
    def _parse_run_completion_status_path(run_completion_status_path: Path) -> ElementTree:
        """Parse the RunInfo.xml file."""
        return read_xml(file_path=run_completion_status_path)

    def get_start_time(self, run_completion_status_path: Path) -> datetime:
        """Get the sequencer start date and time."""
        tree: ElementTree = self._parse_run_completion_status_path(run_completion_status_path)
        return self.format_time(tree.find(RunCompletionStatusNodes.RUN_START).text)

    def get_end_time(self, run_completion_status_path: Path) -> datetime:
        """Get the sequencer end date and time."""
        tree: ElementTree = self._parse_run_completion_status_path(run_completion_status_path)
        return self.format_time(tree.find(RunCompletionStatusNodes.RUN_END).text)
