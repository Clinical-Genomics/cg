from pytest import approx

from cg.meta.demultiplex.create_non_pooled_metrics import weighted_average


def test_calculates_simple_weighted_average():
    # GIVEN: Equal total counts and different percentages
    total_1, percentage_1 = 50, 0.9
    total_2, percentage_2 = 50, 0.7

    # WHEN: Calculating the weighted average
    result: float = weighted_average(
        total_1=total_1, percentage_1=percentage_1, total_2=total_2, percentage_2=percentage_2
    )

    # THEN: The weighted average should be 0.8
    assert result == 0.8


def test_handles_zero_counts():
    # GIVEN: Zero counts for both totals
    total_1, percentage_1 = 0, 0.0
    total_2, percentage_2 = 0, 0.0

    # WHEN: Calculating the weighted average
    result: float = weighted_average(
        total_1=total_1, percentage_1=percentage_1, total_2=total_2, percentage_2=percentage_2
    )

    # THEN: The weighted average should be zero
    assert result == 0.0
