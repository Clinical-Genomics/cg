"""Module to parse the illumina demultiplexing log file."""

from pathlib import Path

from pydantic import BaseModel

from cg.io.json import read_json


class DemuxSoftware(BaseModel):
    software_version: str
    software: str


def _parse_dragen_replay(content: dict) -> DemuxSoftware:
    """Parse a dragen-replay.json file."""
    system_info: dict = content["system"]
    return DemuxSoftware(
        software_version=system_info["dragen_version"],
        software="dragen",
    )


def _parse_highlevel_summary(content: dict) -> DemuxSoftware:
    """Parse a highlevel_summary.json file."""
    return DemuxSoftware(
        software_version=content["software_version"],
        software="dragen",
    )


class IlluminaDemuxVersionService:
    @staticmethod
    def _parse_demux_version_file(demux_version_file: Path) -> DemuxSoftware:
        """Parse the demultiplexing log file."""
        content: dict = read_json(demux_version_file)
        if demux_version_file.name == "highlevel_summary.json":
            return _parse_highlevel_summary(content)
        return _parse_dragen_replay(content)

    def get_demux_software(self, demux_version_file: Path) -> str:
        """Get the demux software."""
        demux_software: DemuxSoftware = self._parse_demux_version_file(demux_version_file)
        return demux_software.software

    def get_demux_software_version(self, demux_version_file: Path) -> str:
        """Get the demultiplexing software version."""
        demux_software: DemuxSoftware = self._parse_demux_version_file(demux_version_file)
        return demux_software.software_version
