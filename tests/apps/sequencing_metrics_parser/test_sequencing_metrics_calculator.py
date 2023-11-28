import pytest

from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    calculate_average_quality_score,
    calculate_q30_bases_percentage,
)


@pytest.mark.parametrize(
    "q30_yield, total_yield, expected_result", [(100, 200, 0.5 * 100), (0, 0, 0)]
)
def test_calculate_bases_with_q30_percentage(
    q30_yield: int, total_yield: int, expected_result: float
):
    """Test calculating q30 ratio."""
    # GIVEN a number of bases with q30 and a total number of bases

    # WHEN calculating the q30 ratio
    q30_percentage = calculate_q30_bases_percentage(q30_yield=q30_yield, total_yield=total_yield)

    # THEN the q30 ratio should be the number of bases with q30 divided by the total number of bases
    assert q30_percentage == expected_result


@pytest.mark.parametrize(
    "total_quality_score, total_yield, expected_result", [(100, 200, 0.5), (0, 0, 0)]
)
def test_calculate_lane_mean_quality_score(
    total_quality_score: int, total_yield: int, expected_result: float
):
    """Test calculating the average quality score."""
    # GIVEN a total quality score and a total yield

    # WHEN calculating the average quality score
    avg_quality_score: float = calculate_average_quality_score(
        total_quality_score=total_quality_score, total_yield=total_yield
    )

    # THEN the average quality score should be the total quality score divided by the total yield
    assert avg_quality_score == expected_result
