from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile


class HiFiParser:
    """Class for parsing HiFi metrics."""

    def _parse_json(self, json_file: Path) -> dict:
        """Parse the JSON file."""
        return ReadFile.read_file[FileFormat.JSON](file_path=json_file)
