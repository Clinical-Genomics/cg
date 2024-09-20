"""Class to parse the content of a sample sheet file."""

from cg.constants.demultiplexing import SampleSheetBCLConvertSections
from cg.services.illumina.sample_sheet.error_handlers import handle_value_and_validation_errors
from cg.services.illumina.sample_sheet.models import (
    IlluminaSampleIndexSetting,
    SampleSheet,
    SampleSheetData,
    SampleSheetHeader,
    SampleSheetReads,
    SampleSheetSettings,
)


class SampleSheetParser:
    """
    Class to parse the content of a sample sheet file into a SampleSheet model or
    IlluminaSampleIndexSetting.
    Exposed functions:
        - parse: Parse a sample sheet content into a SampleSheet model.
        - get_samples_from_data_content: Return a list of IlluminaSampleIndexSetting from the sample
        sheet data content.
    """

    @handle_value_and_validation_errors
    def parse(self, content: list[list[str]]) -> SampleSheet:
        """Parse a sample sheet file content into a SampleSheet model.
        Raises:
            SampleSheetValidationError: if the content does not have the correct structure or values
        """
        header_section, reads_section, settings_section, data_section = (
            self._separate_content_into_sections(content)
        )
        header: SampleSheetHeader = self._get_sample_sheet_header(header_section)
        reads: SampleSheetReads = self._get_sample_sheet_reads(reads_section)
        settings: SampleSheetSettings = self._get_sample_sheet_settings(settings_section)
        data: SampleSheetData = self._get_sample_sheet_data(data_section)
        return SampleSheet(header=header, reads=reads, settings=settings, data=data)

    @staticmethod
    def get_samples_from_data_content(
        data_content: list[list[str]],
    ) -> list[IlluminaSampleIndexSetting]:
        """
        Return parsed samples from the sample sheet data content.
        Raises:
            ValidationError: if the samples do not have the correct model attributes.
        """
        samples: list[IlluminaSampleIndexSetting] = []
        column_names: list[str] = data_content[1]
        for line in data_content[2:]:
            raw_sample = dict(zip(column_names, line))
            samples.append(IlluminaSampleIndexSetting.model_validate(raw_sample))
        return samples

    @staticmethod
    def _separate_content_into_sections(content: list[list[str]]) -> tuple:
        """Separate the content of a sample sheet file into its sections.
        Raises:
            ValueError: If any of the sections is not found in the content.
        """
        header_starts_line: int = content.index([SampleSheetBCLConvertSections.Header.HEADER])
        reads_starts_line: int = content.index([SampleSheetBCLConvertSections.Reads.HEADER])
        settings_starts_line: int = content.index([SampleSheetBCLConvertSections.Settings.HEADER])
        data_starts_line: int = content.index([SampleSheetBCLConvertSections.Data.HEADER])

        header_section: list[list[str]] = content[header_starts_line:reads_starts_line]
        reads_section: list[list[str]] = content[reads_starts_line:settings_starts_line]
        settings_section: list[list[str]] = content[settings_starts_line:data_starts_line]
        data_section: list[list[str]] = content[data_starts_line:]
        return header_section, reads_section, settings_section, data_section

    @staticmethod
    def _get_sample_sheet_header(content: list[list[str]]) -> SampleSheetHeader:
        """
        Return the parsed Header section of the sample sheet given its header content.
        Raises:
            ValidationError: if the content does not have the correct structure and values.
        """
        return SampleSheetHeader(
            version=content[1],
            run_name=content[2],
            instrument=content[3],
            index_orientation=content[4],
            index_settings=content[5],
        )

    @staticmethod
    def _get_sample_sheet_reads(content: list[list[str]]) -> SampleSheetReads:
        """Return the parsed Reads section of the sample sheet given its reads content.
        Raises:
            ValidationError: if the content does not have the correct structure and values.
        """
        reads_section: dict = {
            "read_1": content[1],
            "read_2": content[2],
            "index_1": content[3],
        }
        if len(content) > 4:
            reads_section["index_2"] = content[4]
        return SampleSheetReads.model_validate(reads_section)

    @staticmethod
    def _get_sample_sheet_settings(content: list[list[str]]) -> SampleSheetSettings:
        """Return the parsed Settings section of the sample sheet given its settings content.
        Raises:
            ValidationError: if the content does not have the correct structure and values.
        """
        return SampleSheetSettings(
            software_version=content[1],
            compression_format=content[2],
        )

    def _get_sample_sheet_data(self, content: list[list[str]]) -> SampleSheetData:
        """Return the parsed Data section of the sample sheet given its data content.
        Raises:
            ValidationError: if the content does not have the correct structure and values.
        """
        samples: list[IlluminaSampleIndexSetting] = self.get_samples_from_data_content(content)
        return SampleSheetData(columns=content[1], samples=samples)
