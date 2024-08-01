from pydantic import BaseModel, ConfigDict, Field

from cg.apps.demultiplex.sample_sheet.validators import SampleId
from cg.constants.demultiplexing import SampleSheetBCLConvertSections
from cg.constants.symbols import EMPTY_STRING


class IlluminaSampleIndexSetting(BaseModel):
    """Class that represents index settings for a sample on an Illumina run."""

    lane: int = Field(..., alias=SampleSheetBCLConvertSections.Data.LANE)
    sample_id: SampleId = Field(..., alias=SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID)
    index: str = Field(..., alias=SampleSheetBCLConvertSections.Data.INDEX_1)
    index2: str | None = Field(None, alias=SampleSheetBCLConvertSections.Data.INDEX_2)
    override_cycles: str = Field(
        EMPTY_STRING, alias=SampleSheetBCLConvertSections.Data.OVERRIDE_CYCLES
    )
    barcode_mismatches_1: int = Field(
        1, alias=SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_1
    )
    barcode_mismatches_2: int | str | None = Field(
        None, alias=SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_2
    )
    model_config = ConfigDict(populate_by_name=True)


class SampleSheetSection(BaseModel):
    """Base class for a section of a sample sheet."""

    def as_content(self) -> list[list[str]]:
        """Return the content of the section as a list of lists."""
        return [list(self.model_dump(exclude_none=True).values())]


class SampleSheetHeader(SampleSheetSection):
    header: list[str] = Field([SampleSheetBCLConvertSections.Header.HEADER], frozen=True)
    version: list[str]
    run_name: list[str]
    instrument: list[str]
    index_orientation: list[str]
    index_settings: list[str]


class SampleSheetReads(SampleSheetSection):
    header: list[str] = Field([SampleSheetBCLConvertSections.Reads.HEADER], frozen=True)
    read_1: list[str]
    read_2: list[str]
    index_1: list[str]
    index_2: list[str] | None


class SampleSheetSettings(SampleSheetSection):
    header: list[str] = Field([SampleSheetBCLConvertSections.Settings.HEADER], frozen=True)
    software_version: list[str]
    compression_format: list[str]


class SampleSheetData(SampleSheetSection):
    header: list[str] = Field([SampleSheetBCLConvertSections.Data.HEADER], frozen=True)
    columns: list[str]
    samples: list[IlluminaSampleIndexSetting]

    def as_content(self) -> list[list[str]]:
        """Return the content of the data section as a list of lists."""
        content: list[list[str]] = [self.header, self.columns]
        for sample in self.samples:
            content.append(list(sample.model_dump(exclude_none=True).values()))
        return content


class SampleSheet(BaseModel):
    header: SampleSheetHeader
    reads: SampleSheetReads
    settings: SampleSheetSettings
    data: SampleSheetData

    def get_content(self) -> list[list[str]]:
        """Return the content of the sample sheet as a list of lists."""
        content: list[list[str]] = (
            self.header.as_content()
            + self.reads.as_content()
            + self.settings.as_content()
            + self.data.as_content()
        )
        return content
