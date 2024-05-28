"""Module to parse the illumina demultiplexing log file."""

from pathlib import Path

from cg.constants import SPACE
from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile


class IlluminaDemuxVersionService:

    @staticmethod
    def _parse_demux_version_file(demux_version_file: Path) -> list[str]:
        """Parse the demultiplexing log file."""
        reader = ReadFile()
        return reader.get_content_from_file(
            file_path=demux_version_file, file_format=FileFormat.TXT
        )

    def get_dragen_software_info(self, demux_version_file: Path):
        """Get first line of the demux version file and remove new line."""
        for line in self._parse_demux_version_file(demux_version_file):
            return line.replace("\n", "")

    def get_demux_software(self, demux_version_file: Path) -> str:
        """Get the demultiplexing software used."""
        return self.get_dragen_software_info(demux_version_file).split(SPACE)[0]

    def get_demux_software_version(self, demux_version_file: Path) -> str:
        """Get the demultiplexing software version."""
        return self.get_dragen_software_info(demux_version_file).split(SPACE)[-1]
