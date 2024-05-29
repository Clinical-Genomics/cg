"""Module to parse the illumina demultiplexing log file."""

from pathlib import Path

from pydantic import BaseModel, Field

from cg.constants import SPACE
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.io.json import read_json


class DemuxSoftware(BaseModel):
    software_version: str = Field(..., alias="dragen_version")
    software: str = Field(default="dragen")


class IlluminaDemuxVersionService:

    @staticmethod
    def _parse_demux_version_file(demux_version_file: Path) -> DemuxSoftware:
        """Parse the demultiplexing log file."""
        content = read_json(demux_version_file)
        system_info: dict = content.get("system")
        return DemuxSoftware(**system_info)

    def get_demux_software(self, demux_version_file: Path):
        """Get first line of the demux version file and remove new line."""
        demux_software: DemuxSoftware = self._parse_demux_version_file(demux_version_file)
        return demux_software.software

    def get_demux_software_version(self, demux_version_file: Path) -> str:
        """Get the demultiplexing software version."""
        demux_software: DemuxSoftware = self._parse_demux_version_file(demux_version_file)
        return demux_software.software_version
