import re
from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel, BeforeValidator, Field, model_validator
from typing_extensions import Annotated

from cg.constants.pacbio import (
    BarcodeMetricsAliases,
    CCSAttributeAliases,
    ControlAttributeAliases,
    LoadingAttributesAliases,
    PolymeraseDataAttributeAliases,
    SampleMetricsAliases,
    SmrtLinkDatabasesAliases,
)
from cg.services.run_devices.abstract_models import RunMetrics
from cg.utils.calculations import fraction_to_percent

BaseMetrics = TypeVar("BaseMetrics", bound=BaseModel)


class ReadMetrics(BaseModel):
    """Model for the read metrics."""

    hifi_reads: int = Field(..., alias=CCSAttributeAliases.HIFI_READS)
    hifi_yield: int = Field(..., alias=CCSAttributeAliases.HIFI_YIELD)
    hifi_mean_read_length: int = Field(..., alias=CCSAttributeAliases.HIFI_MEAN_READ_LENGTH)
    hifi_median_read_length: int = Field(..., alias=CCSAttributeAliases.HIFI_MEDIAN_READ_LENGTH)
    hifi_mean_length_n50: int = Field(..., alias=CCSAttributeAliases.HIFI_READ_LENGTH_N50)
    hifi_median_read_quality: int = Field(..., alias=CCSAttributeAliases.HIFI_MEDIAN_READ_QUALITY)
    percent_q30: float = Field(..., alias=CCSAttributeAliases.PERCENT_Q30)
    failed_reads: int = Field(..., alias=CCSAttributeAliases.FAILED_READS)
    failed_yield: int = Field(..., alias=CCSAttributeAliases.FAILED_YIELD)
    failed_mean_read_length: int = Field(..., alias=CCSAttributeAliases.FAILED_MEAN_READ_LENGTH)


class ControlMetrics(BaseModel):
    """Model for the control metrics."""

    reads: int = Field(..., alias=ControlAttributeAliases.NUMBER_OF_READS)
    mean_read_length: int = Field(..., alias=ControlAttributeAliases.MEAN_READ_LENGTH)
    percent_mean_concordance_reads: Annotated[float, BeforeValidator(fraction_to_percent)] = Field(
        ..., alias=ControlAttributeAliases.PERCENT_MEAN_READ_CONCORDANCE
    )
    percent_mode_concordance_reads: Annotated[float, BeforeValidator(fraction_to_percent)] = Field(
        ..., alias=ControlAttributeAliases.PERCENT_MODE_READ_CONCORDANCE
    )


class ProductivityMetrics(BaseModel):
    """Model for the loading metrics."""

    productive_zmws: int = Field(..., alias=LoadingAttributesAliases.PRODUCTIVE_ZMWS)
    p_0: int = Field(..., alias=LoadingAttributesAliases.P_0)
    p_1: int = Field(..., alias=LoadingAttributesAliases.P_1)
    p_2: int = Field(..., alias=LoadingAttributesAliases.P_2)
    percent_p_0: float
    percent_p_1: float
    percent_p_2: float

    @model_validator(mode="before")
    @classmethod
    def set_percentages(cls, data: Any):
        if isinstance(data, dict):
            productive_zmws = data.get(LoadingAttributesAliases.PRODUCTIVE_ZMWS)
            p_0 = data.get(LoadingAttributesAliases.P_0)
            p_1 = data.get(LoadingAttributesAliases.P_1)
            p_2 = data.get(LoadingAttributesAliases.P_2)
            data["percent_p_0"] = round((p_0 / productive_zmws) * 100, 0)
            data["percent_p_1"] = round((p_1 / productive_zmws) * 100, 0)
            data["percent_p_2"] = round((p_2 / productive_zmws) * 100, 0)
        return data


class PolymeraseMetrics(BaseModel):
    """Model for the polymerase metrics."""

    mean_read_length: int = Field(..., alias=PolymeraseDataAttributeAliases.MEAN_READ_LENGTH)
    read_length_n50: int = Field(..., alias=PolymeraseDataAttributeAliases.READ_LENGTH_N50)
    mean_longest_subread_length: int = Field(
        ..., alias=PolymeraseDataAttributeAliases.MEAN_LONGEST_SUBREAD_LENGTH
    )
    longest_subread_length_n50: int = Field(
        ..., alias=PolymeraseDataAttributeAliases.LONGEST_SUBREAD_LENGTH_N50
    )


class SmrtlinkDatasetsMetrics(BaseModel):
    """Model to parse metrics in the SMRTlink datasets report."""

    cell_id: str = Field(..., alias=SmrtLinkDatabasesAliases.CELL_ID)
    well: str = Field(..., alias=SmrtLinkDatabasesAliases.WELL_NAME)
    well_sample_name: str = Field(..., alias=SmrtLinkDatabasesAliases.WELL_SAMPLE_NAME)
    run_started_at: datetime
    run_completed_at: datetime = Field(..., alias=SmrtLinkDatabasesAliases.RUN_COMPLETED_AT)
    movie_name: str = Field(..., alias=SmrtLinkDatabasesAliases.MOVIE_NAME)
    cell_index: int = Field(..., alias=SmrtLinkDatabasesAliases.CELL_INDEX)
    path: str = Field(..., alias=SmrtLinkDatabasesAliases.PATH)
    plate: int

    @model_validator(mode="before")
    @classmethod
    def extract_plate(cls, data: Any):
        if isinstance(data, dict):
            path = data.get("path")
            if path:
                pattern = r"/([12])_[ABCD]01"
                match = re.search(pattern, path)
                if match:
                    data["plate"] = match.group(1)
        return data

    @model_validator(mode="before")
    @classmethod
    def set_sequencing_completed_at(cls, data: Any):
        if isinstance(data, dict):
            movie_name = data.get(SmrtLinkDatabasesAliases.MOVIE_NAME)
            if movie_name:
                date: str = movie_name.split("_")[1] + movie_name.split("_")[2]
                data["run_started_at"] = datetime.strptime(date, "%y%m%d%H%M%S")
        return data


class BarcodeMetrics(RunMetrics):
    """Model that holds barcode data."""

    barcoded_hifi_reads: int = Field(..., alias=BarcodeMetricsAliases.BARCODED_HIFI_READS)
    barcoded_hifi_reads_percentage: Annotated[float, BeforeValidator(fraction_to_percent)] = Field(
        ..., alias=BarcodeMetricsAliases.BARCODED_HIFI_READS_PERCENTAGE
    )
    barcoded_hifi_yield: int = Field(..., alias=BarcodeMetricsAliases.BARCODED_HIFI_YIELD)
    barcoded_hifi_yield_percentage: Annotated[float, BeforeValidator(fraction_to_percent)] = Field(
        ..., alias=BarcodeMetricsAliases.BARCODED_HIFI_YIELD_PERCENTAGE
    )
    barcoded_hifi_mean_read_length: int = Field(
        ..., alias=BarcodeMetricsAliases.UNBARCODED_HIFI_MEAN_READ_LENGTH
    )
    unbarcoded_hifi_reads: int = Field(..., alias=BarcodeMetricsAliases.UNBARCODED_HIFI_READS)
    unbarcoded_hifi_yield: int = Field(..., alias=BarcodeMetricsAliases.UNBARCODED_HIFI_YIELD)
    unbarcoded_hifi_mean_read_length: int = Field(
        ..., alias=BarcodeMetricsAliases.UNBARCODED_HIFI_MEAN_READ_LENGTH
    )


class SampleMetrics(RunMetrics):
    """Model that holds run data for a specific sample."""

    barcode_name: str = Field(..., alias=SampleMetricsAliases.BARCODE_NAME)
    hifi_mean_read_length: int = Field(..., alias=SampleMetricsAliases.HIFI_MEAN_READ_LENGTH)
    hifi_median_read_quality: str = Field(..., alias=SampleMetricsAliases.HIFI_READ_QUALITY)
    hifi_reads: int = Field(..., alias=SampleMetricsAliases.HIFI_READS)
    hifi_yield: int = Field(..., alias=SampleMetricsAliases.HIFI_YIELD)
    polymerase_read_length: int = Field(..., alias=SampleMetricsAliases.POLYMERASE_READ_LENGTH)
    sample_internal_id: str = Field(..., alias=SampleMetricsAliases.SAMPLE_INTERNAL_ID)


class PacBioMetrics(RunMetrics):
    """Model that holds all relevant PacBio metrics."""

    read: ReadMetrics
    control: ControlMetrics
    productivity: ProductivityMetrics
    polymerase: PolymeraseMetrics
    dataset_metrics: SmrtlinkDatasetsMetrics
    barcodes: BarcodeMetrics
    samples: list[SampleMetrics]
