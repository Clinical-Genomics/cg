"""Module to get the sequencing completed service."""

from datetime import datetime
from pathlib import Path


class SequencingCompletedService:
    """Class to get the sequencing completed service."""

    def get_end_time(self, sequence_completed_path: Path) -> datetime:
        """Get the sequencer end date and time."""
