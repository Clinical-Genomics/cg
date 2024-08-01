from pathlib import Path

from cg.constants.constants import FileFormat
from cg.io.controller import ReadFile
from cg.services.illumina.sample_sheet.parser import SampleSheetParser


class SampleSheetValidator:

    def __init__(self, parser: SampleSheetParser) -> None:
        self.parser = parser

    def validate_file(self, file_path: Path) -> None:
        """Validate a sample sheet given the path to the file."""
        content: list[list[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=file_path
        )
        self.validate_content(content=content)

    def validate_content(self, content: list[list[str]]) -> None:
        """Validate the content of a sample sheet."""
        sample_sheet = self.parser.parse(content)
        self._validate_header(sample_sheet.header)
        self._validate_reads(sample_sheet.reads)
        self._validate_settings(sample_sheet.settings)
        self._validate_data(sample_sheet.data)
