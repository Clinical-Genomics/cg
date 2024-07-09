from pydantic import BaseModel, Field, field_validator

from cg.constants.pacbio import (
    CCSAttributeIDs,
    ControlAttributeIDs,
    LoadingAttributesIDs,
    PolymeraseDataAttributeIDs,
)
from cg.utils.calculations import divide_by_thousand_with_one_decimal, fraction_to_percent


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

    @property
    def percentage_p_0(self) -> float:
        return self._calculate_percentage(self.p_0)

    @property
    def percentage_p_1(self) -> float:
        return self._calculate_percentage(self.p_1)

    @property
    def percentage_p_2(self) -> float:
        return self._calculate_percentage(self.p_2)

    def _calculate_percentage(self, value: int) -> float:
        """Calculates the percentage of a value to productive_zmws."""
        if self.productive_zmws == 0:
            return 0.0
        return round((value / self.productive_zmws) * 100, 0)


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
