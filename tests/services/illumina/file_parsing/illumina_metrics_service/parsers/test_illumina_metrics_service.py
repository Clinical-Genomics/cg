"""Test for service dtos."""

import pytest

from cg.services.illumina.data_transfer.data_transfer_service import (
    IlluminaSampleSequencingMetricsDTO,
    IlluminaSequencingRunDTO,
)


@pytest.mark.parametrize(
    "percent_value, expected",
    [
        (0.94, 94.0),
        (94.0, 94.0),
        (0.005, 0.5),
    ],
)
def test_percent_validators_sequencing_dto(
    empty_illumina_sequencing_dto: IlluminaSequencingRunDTO, percent_value: float, expected: float
):
    """Test that the percentage validation works."""
    # GIVEN an input value for a DTO percentage attribute

    # WHEN assigning the value to the DTO attributes
    empty_illumina_sequencing_dto.percent_undetermined_reads = percent_value
    empty_illumina_sequencing_dto.percent_q30 = percent_value

    # THEN the value should be converted to a percentage
    assert empty_illumina_sequencing_dto.percent_undetermined_reads == expected
    assert empty_illumina_sequencing_dto.percent_q30 == expected


@pytest.mark.parametrize(
    "percent_value, expected",
    [
        (0.94, 94.0),
        (94.0, 94.0),
        (0.005, 0.5),
    ],
)
def test_percent_validator_sample_sequencing_metrics_dto(
    combined_metric: IlluminaSampleSequencingMetricsDTO,
    percent_value: float,
    expected: float,
):
    """Test that the percentage validation works."""
    # GIVEN an input value for a DTO percentage attribute

    # WHEN assigning the value to the DTO attributes
    combined_metric.base_passing_q30_percent = percent_value

    # THEN the value should be converted to a percentage
    assert combined_metric.base_passing_q30_percent == expected
