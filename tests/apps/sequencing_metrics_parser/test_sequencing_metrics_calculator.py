from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    calculate_q30_bases_percentage,
    calculate_average_quality_score,
)


def test_calculate_bases_with_q30_percentage():
    """Test calculating q30 ratio."""
    # GIVEN a number of bases with q30 and a total number of bases
    q30_yield: int = 100
    total_yield: int = 200

    # WHEN calculating the q30 ratio
    q30_percentage = calculate_q30_bases_percentage(q30_yield=q30_yield, total_yield=total_yield)

    # THEN the q30 ratio should be the number of bases with q30 divided by the total number of bases
    assert q30_percentage == (q30_yield / total_yield) * 100


def test_calculate_lane_mean_quality_score():
    """Test calculating the average quality score."""
    # GIVEN a total quality score and a total yield
    total_quality_score: int = 100
    total_yield: int = 200

    # WHEN calculating the average quality score
    avg_quality_score: float = calculate_average_quality_score(
        total_quality_score=total_quality_score, total_yield=total_yield
    )

    # THEN the average quality score should be the total quality score divided by the total yield
    assert avg_quality_score == total_quality_score / total_yield
