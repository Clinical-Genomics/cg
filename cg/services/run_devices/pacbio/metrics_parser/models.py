import re
from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

from cg.constants.pacbio import (
    CCSAttributeIDs,
    ControlAttributeIDs,
    LoadingAttributesIDs,
    PolymeraseDataAttributeIDs,
    SmrtLinkDatabasesIDs,
)
from cg.services.run_devices.abstract_models import RunMetrics
from cg.utils.calculations import fraction_to_percent

BaseMetrics = TypeVar("BaseMetrics", bound=BaseModel)


class ReadMetrics(BaseModel):
    """Model for the read metrics."""

    hifi_reads: int = Field(..., alias=CCSAttributeIDs.HIFI_READS)
    hifi_yield: int = Field(..., alias=CCSAttributeIDs.HIFI_YIELD)
    hifi_mean_read_length: int = Field(..., alias=CCSAttributeIDs.HIFI_MEAN_READ_LENGTH)
    hifi_median_read_length: int = Field(..., alias=CCSAttributeIDs.HIFI_MEDIAN_READ_LENGTH)
    hifi_mean_length_n50: int = Field(..., alias=CCSAttributeIDs.HIFI_READ_LENGTH_N50)
    hifi_median_read_quality: int = Field(..., alias=CCSAttributeIDs.HIFI_MEDIAN_READ_QUALITY)
    percent_q30: float = Field(..., alias=CCSAttributeIDs.PERCENT_Q30)
    failed_reads: int = Field(..., alias=CCSAttributeIDs.FAILED_READS)
    failed_yield: int = Field(..., alias=CCSAttributeIDs.FAILED_YIELD)
    failed_mean_read_length: int = Field(..., alias=CCSAttributeIDs.FAILED_MEAN_READ_LENGTH)


class ControlMetrics(BaseModel):
    """Model for the control metrics."""

    reads: int = Field(..., alias=ControlAttributeIDs.NUMBER_OF_READS)
    mean_read_length: int = Field(..., alias=ControlAttributeIDs.MEAN_READ_LENGTH)
    percent_mean_concordance_reads: float = Field(
        ..., alias=ControlAttributeIDs.PERCENT_MEAN_READ_CONCORDANCE
    )
    percent_mode_concordance_reads: float = Field(
        ..., alias=ControlAttributeIDs.PERCENT_MODE_READ_CONCORDANCE
    )

    _validate_percent_mean_concordance_reads = field_validator(
        "percent_mean_concordance_reads", mode="before"
    )(fraction_to_percent)

    _validate_percent_mode_concordance_reads = field_validator(
        "percent_mode_concordance_reads", mode="before"
    )(fraction_to_percent)


class ProductivityMetrics(BaseModel):
    """Model for the loading metrics."""

    productive_zmws: int = Field(..., alias=LoadingAttributesIDs.PRODUCTIVE_ZMWS)
    p_0: int = Field(..., alias=LoadingAttributesIDs.P_0)
    p_1: int = Field(..., alias=LoadingAttributesIDs.P_1)
    p_2: int = Field(..., alias=LoadingAttributesIDs.P_2)
    percent_p_0: float
    percent_p_1: float
    percent_p_2: float

    @model_validator(mode="before")
    @classmethod
    def set_percentages(cls, data: Any):
        if isinstance(data, dict):
            productive_zmws = data.get(LoadingAttributesIDs.PRODUCTIVE_ZMWS)
            p_0 = data.get(LoadingAttributesIDs.P_0)
            p_1 = data.get(LoadingAttributesIDs.P_1)
            p_2 = data.get(LoadingAttributesIDs.P_2)
            data["percent_p_0"] = round((p_0 / productive_zmws) * 100, 0)
            data["percent_p_1"] = round((p_1 / productive_zmws) * 100, 0)
            data["percent_p_2"] = round((p_2 / productive_zmws) * 100, 0)
        return data


class PolymeraseMetrics(BaseModel):
    """Model for the polymerase metrics."""

    mean_read_length: int = Field(..., alias=PolymeraseDataAttributeIDs.MEAN_READ_LENGTH)
    read_length_n50: int = Field(..., alias=PolymeraseDataAttributeIDs.READ_LENGTH_N50)
    mean_longest_subread_length: int = Field(
        ..., alias=PolymeraseDataAttributeIDs.MEAN_LONGEST_SUBREAD_LENGTH
    )
    longest_subread_length_n50: int = Field(
        ..., alias=PolymeraseDataAttributeIDs.LONGEST_SUBREAD_LENGTH_N50
    )


class SmrtlinkDatasetsMetrics(BaseModel):
    """Model to parse metrics in the SMRTlink datasets report."""

    cell_id: str = Field(..., alias=SmrtLinkDatabasesIDs.CELL_ID)
    well: str = Field(..., alias=SmrtLinkDatabasesIDs.WELL_NAME)
    well_sample_name: str = Field(..., alias=SmrtLinkDatabasesIDs.WELL_SAMPLE_NAME)
    sample_internal_id: str = Field(..., alias=SmrtLinkDatabasesIDs.BIO_SAMPLE_NAME)
    run_started_at: datetime
    run_completed_at: datetime = Field(..., alias=SmrtLinkDatabasesIDs.RUN_COMPLETED_AT)
    movie_name: str = Field(..., alias=SmrtLinkDatabasesIDs.MOVIE_NAME)
    cell_index: int = Field(..., alias=SmrtLinkDatabasesIDs.CELL_INDEX)
    path: str = Field(..., alias=SmrtLinkDatabasesIDs.PATH)
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
            movie_name = data.get(SmrtLinkDatabasesIDs.MOVIE_NAME)
            if movie_name:
                date: str = movie_name.split("_")[1] + movie_name.split("_")[2]
                data["run_started_at"] = datetime.strptime(date, "%y%m%d%H%M%S")
        return data


class PacBioMetrics(RunMetrics):
    """Model that holds all relevant PacBio metrics."""

    read: ReadMetrics
    control: ControlMetrics
    productivity: ProductivityMetrics
    polymerase: PolymeraseMetrics
    dataset_metrics: SmrtlinkDatasetsMetrics
