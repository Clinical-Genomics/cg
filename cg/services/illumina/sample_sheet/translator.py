from cg.constants.demultiplexing import SampleSheetBcl2FastqSections, SampleSheetBCLConvertSections
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData
from cg.services.illumina.sample_sheet.creator import SampleSheetCreator
from cg.services.illumina.sample_sheet.models import IlluminaSampleIndexSetting, SampleSheet
from cg.services.illumina.sample_sheet.parser import SampleSheetParser


class SampleSheetTranslator:

    def __init__(self, creator: SampleSheetCreator, parser: SampleSheetParser):
        self.creator = creator
        self.parser = parser

    def translate_content(
        self, content: list[list[str]], run_dir: IlluminaRunDirectoryData
    ) -> list[list[str]]:
        """Create a BCLConvert sample sheet given the content of a BCL2Fastq sample sheet."""
        fixed_content: list[list[str]] = self._replace_sample_header(sample_sheet_content=content)
        data_content: list[list[str]] = self._get_data_content(content=fixed_content)
        samples: list[IlluminaSampleIndexSetting] = self.parser.get_samples_from_data_content(
            data_content=data_content
        )
        sample_sheet: SampleSheet = self.creator.create(run_dir=run_dir, samples=samples)
        return sample_sheet.get_content()

    @staticmethod
    def _get_data_content(content: list[list[str]]) -> list[list[str]]:
        """Get the data section of the sample sheet."""
        data_index: int = content.index([SampleSheetBcl2FastqSections.Data.HEADER])
        return content[data_index:]

    @staticmethod
    def _replace_sample_header(sample_sheet_content: list[list[str]]) -> list[list[str]]:
        """
        Replace the old sample ID header in the Bcl2Fastq sample sheet content with the BCLConvert
        formatted one.
        Raises:
            SampleSheetFormatError: If the data header is not found in the sample sheet.
        """
        # TODO: verify if the index(es) need to be changed too
        pattern: str = SampleSheetBcl2FastqSections.Data.SAMPLE_INTERNAL_ID_BCL2FASTQ
        for line in sample_sheet_content:
            if pattern in line:
                idx: int = line.index(pattern)
                line[idx] = SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID
                return sample_sheet_content
        # TODO: Add custom exception
        raise ValueError("Data header not found in sample sheet content")
