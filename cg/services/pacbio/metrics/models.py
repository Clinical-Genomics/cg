import re
from typing import Any, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

from cg.constants.pacbio import (
    CCSAttributeIDs,
    ControlAttributeIDs,
    LoadingAttributesIDs,
    PolymeraseDataAttributeIDs,
    SmrtLinkDatabasesIDs,
)
from cg.utils.calculations import divide_by_thousand_with_one_decimal, fraction_to_percent

BaseMetrics = TypeVar("BaseMetrics", bound=BaseModel)


class HiFiMetrics(BaseModel):
    """Model for the HiFi metrics."""

    reads: int = Field(..., alias=CCSAttributeIDs.NUMBER_OF_READS)
    yield_: int = Field(..., alias=CCSAttributeIDs.TOTAL_NUMBER_OF_BASES)
    mean_read_length_kb: float = Field(..., alias=CCSAttributeIDs.MEAN_READ_LENGTH)
    median_read_length: int = Field(..., alias=CCSAttributeIDs.MEDIAN_READ_LENGTH)
    mean_length_n50: int = Field(..., alias=CCSAttributeIDs.READ_LENGTH_N50)
    median_read_quality: str = Field(..., alias=CCSAttributeIDs.MEDIAN_ACCURACY)
    percent_q30: float = Field(..., alias=CCSAttributeIDs.PERCENT_Q30)

    _validate_mean_read_length_kb = field_validator("mean_read_length_kb", mode="before")(
        divide_by_thousand_with_one_decimal
    )
    _validate_percent_q30 = field_validator("percent_q30", mode="before")(fraction_to_percent)


class ControlMetrics(BaseModel):
    """Model for the control metrics."""

    reads: int = Field(..., alias=ControlAttributeIDs.NUMBER_OF_READS)
    mean_read_length_kb: float = Field(..., alias=ControlAttributeIDs.MEAN_READ_LENGTH)
    percent_mean_concordance_reads: float = Field(
        ..., alias=ControlAttributeIDs.PERCENT_MEAN_READ_CONCORDANCE
    )
    percent_mode_concordance_reads: float = Field(
        ..., alias=ControlAttributeIDs.PERCENT_MODE_READ_CONCORDANCE
    )

    _validate_mean_read_length_kb = field_validator("mean_read_length_kb", mode="before")(
        divide_by_thousand_with_one_decimal
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

    mean_read_length: float = Field(..., alias=PolymeraseDataAttributeIDs.MEAN_READ_LENGTH)
    read_length_n50: float = Field(..., alias=PolymeraseDataAttributeIDs.READ_LENGTH_N50)
    mean_longest_subread_length: float = Field(
        ..., alias=PolymeraseDataAttributeIDs.MEAN_LONGEST_SUBREAD_LENGTH
    )
    longest_subread_length_n50: float = Field(
        ..., alias=PolymeraseDataAttributeIDs.LONGEST_SUBREAD_LENGTH_N50
    )

    _validate_mean_read_length = field_validator("mean_read_length", mode="before")(
        divide_by_thousand_with_one_decimal
    )
    _validate_read_length_n50 = field_validator("read_length_n50", mode="before")(
        divide_by_thousand_with_one_decimal
    )
    _validate_mean_longest_subread_length = field_validator(
        "mean_longest_subread_length", mode="before"
    )(divide_by_thousand_with_one_decimal)
    _validate_longest_subread_length_n50 = field_validator(
        "longest_subread_length_n50", mode="before"
    )(divide_by_thousand_with_one_decimal)


class SmrtlinkDatasetsMetrics(BaseModel):
    """Model to parse metrics in the SMRTlink datasets report."""

    cell_id: str = Field(..., alias=SmrtLinkDatabasesIDs.CELL_ID)
    well: str = Field(..., alias=SmrtLinkDatabasesIDs.WELL_NAME)
    well_sample_name: str = Field(..., alias=SmrtLinkDatabasesIDs.WELL_SAMPLE_NAME)
    sample_internal_id: str = Field(..., alias=SmrtLinkDatabasesIDs.BIO_SAMPLE_NAME)
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


class PacBioMetrics(BaseModel):
    """Model that holds all relevant PacBio metrics."""

    hifi: HiFiMetrics
    control: ControlMetrics
    productivity: ProductivityMetrics
    polymerase: PolymeraseMetrics
    dataset_metrics: SmrtlinkDatasetsMetrics
