from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cg.apps.demultiplex.sample_sheet.validators import SampleId
from cg.constants.demultiplexing import CUSTOM_INDEX_TAIL, SampleSheetBCLConvertSections
from cg.constants.symbols import EMPTY_STRING
from cg.services.illumina.sample_sheet.utils import (
    field_default_value_validation,
    field_list_elements_validation,
    is_dual_index,
)


class IlluminaSampleIndexSetting(BaseModel):
    """Class that represents index settings for a sample on an Illumina run."""

    lane: int = Field(..., alias=SampleSheetBCLConvertSections.Data.LANE)
    sample_id: SampleId = Field(..., alias=SampleSheetBCLConvertSections.Data.SAMPLE_INTERNAL_ID)
    index: str = Field(..., alias=SampleSheetBCLConvertSections.Data.INDEX_1)
    index2: str | None = Field(None, alias=SampleSheetBCLConvertSections.Data.INDEX_2)
    override_cycles: str = Field(
        EMPTY_STRING, alias=SampleSheetBCLConvertSections.Data.OVERRIDE_CYCLES
    )
    barcode_mismatches_1: int | None = Field(
        None, alias=SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_1
    )
    barcode_mismatches_2: int | str | None = Field(
        None, alias=SampleSheetBCLConvertSections.Data.BARCODE_MISMATCHES_2
    )
    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def separate_indexes(cls, data: any):
        if isinstance(data, dict):
            index = data.get("index")
            if is_dual_index(index):
                index1, index2 = index.split("-")
                data["index"] = index1.strip().replace(CUSTOM_INDEX_TAIL, EMPTY_STRING)
                data["index2"] = index2.strip() if index2 else None
        return data


class SampleSheetSection(BaseModel):
    """Base class for a section of a sample sheet."""

    def as_content(self) -> list[list[str]]:
        """Return the content of the section as a list of lists."""
        return list(self.model_dump(exclude_none=True).values())


class SampleSheetHeader(SampleSheetSection):
    header: list[str] = Field([SampleSheetBCLConvertSections.Header.HEADER], frozen=True)
    version: list[str] = Field(SampleSheetBCLConvertSections.Header.file_format())
    run_name: list[str]
    instrument: list[str]
    index_orientation: list[str] = Field(
        SampleSheetBCLConvertSections.Header.index_orientation_forward()
    )
    index_settings: list[str]

    @field_validator("version", mode="before")
    def validate_version(cls, value):
        default: list[str] = SampleSheetBCLConvertSections.Header.file_format()
        return field_default_value_validation(attribute="version", value=value, default=default)

    @field_validator("run_name")
    def validate_run_name(cls, value):
        name: str = SampleSheetBCLConvertSections.Header.RUN_NAME
        return field_list_elements_validation(attribute="run_name", value=value, name=name)

    @field_validator("instrument")
    def validate_instrument(cls, value):
        name: str = SampleSheetBCLConvertSections.Header.INSTRUMENT_PLATFORM_TITLE
        field_list_elements_validation(attribute="instrument", value=value, name=name)
        allowed_values = list(
            SampleSheetBCLConvertSections.Header.instrument_platform_sequencer().values()
        )
        if value[1] not in allowed_values:
            raise ValueError(f"Invalid instrument platform: {value[1]}")

    @field_validator("index_orientation")
    def validate_index_orientation(cls, value):
        default: list[str] = SampleSheetBCLConvertSections.Header.index_orientation_forward()
        return field_default_value_validation(
            attribute="index_orientation", value=value, default=default
        )

    @field_validator("index_settings")
    def validate_index_settings(cls, value):
        name: str = SampleSheetBCLConvertSections.Header.INDEX_SETTINGS
        return field_list_elements_validation(attribute="index_settings", value=value, name=name)


class SampleSheetReads(SampleSheetSection):
    header: list[str] = Field([SampleSheetBCLConvertSections.Reads.HEADER], frozen=True)
    read_1: list[str]
    read_2: list[str]
    index_1: list[str]
    index_2: list[str] | None

    @field_validator("read_1")
    def validate_read_1(cls, value):
        name: str = SampleSheetBCLConvertSections.Reads.READ_CYCLES_1
        return field_list_elements_validation(attribute="read_1", value=value, name=name)

    @field_validator("read_2")
    def validate_read_2(cls, value):
        name: str = SampleSheetBCLConvertSections.Reads.READ_CYCLES_2
        return field_list_elements_validation(attribute="read_2", value=value, name=name)

    @field_validator("index_1")
    def validate_index_1(cls, value):
        name: str = SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_1
        return field_list_elements_validation(attribute="index_1", value=value, name=name)

    @field_validator("index_2", mode="before")
    def validate_index_2(cls, value):
        name: str = SampleSheetBCLConvertSections.Reads.INDEX_CYCLES_2
        if value is not None:
            return field_list_elements_validation(attribute="index_2", value=value, name=name)


class SampleSheetSettings(SampleSheetSection):
    header: list[str] = Field([SampleSheetBCLConvertSections.Settings.HEADER], frozen=True)
    software_version: list[str] = Field(SampleSheetBCLConvertSections.Settings.software_version())
    compression_format: list[str] = Field(
        SampleSheetBCLConvertSections.Settings.fastq_compression_format()
    )

    @field_validator("software_version")
    def validate_software_version(cls, value):
        default: list[str] = SampleSheetBCLConvertSections.Settings.software_version()
        return field_default_value_validation(
            attribute="software_version", value=value, default=default
        )

    @field_validator("compression_format")
    def validate_compression_format(cls, value):
        default: list[str] = SampleSheetBCLConvertSections.Settings.fastq_compression_format()
        return field_default_value_validation(
            attribute="compression_format", value=value, default=default
        )


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
