from pathlib import Path

from cg.constants.constants import FileFormat
from cg.constants.demultiplexing import SampleSheetBcl2FastqSections
from cg.io.controller import ReadFile
from cg.services.illumina.sample_sheet.parser import SampleSheetParser


class SampleSheetValidator:

    def __init__(self, parser: SampleSheetParser) -> None:
        self.parser = parser

    @staticmethod
    def is_sample_sheet_bcl2fastq(content: list[list[str]]) -> bool:
        """Validate that the sample sheet is not BCL2Fastq."""
        try:
            content.index([SampleSheetBcl2FastqSections.Data.HEADER])
            return True
        # TODO: Add custom exception and error message
        except ValueError:
            return False

    def validate_file(self, file_path: Path) -> None:
        """Validate a sample sheet given the path to the file."""
        content: list[list[str]] = ReadFile.get_content_from_file(
            file_format=FileFormat.CSV, file_path=file_path
        )
        if self.is_sample_sheet_bcl2fastq(content=content):
            raise ValueError("Sample sheet is BCL2Fastq")
        self.validate_content(content=content)

    def validate_content(self, content: list[list[str]]) -> None:
        """Validate the content of a sample sheet."""
        try:
            self.parser.parse(content)
        # TODO: Add custom exception and improve error message
        except ValueError as error:
            raise ValueError(f"Invalid sample sheet content: {error}")
