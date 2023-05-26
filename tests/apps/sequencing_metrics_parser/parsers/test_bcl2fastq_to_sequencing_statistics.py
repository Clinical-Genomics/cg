from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq_to_sequencing_statistics import (
    calculate_average_quality_score_for_sample_in_lane,
    calculate_q30_ratio_for_sample_in_lane,
)
from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import ConversionResult, DemuxResult


def test_calculate_average_quality_score(conversion_result: ConversionResult):
    """ "Test calculating the average quality score from a conversion result."""
    # GIVEN a conversion result with a known average quality score
    for read in conversion_result.demux_results[0].read_metrics:
        read.quality_score_sum = 100
        read.yield_ = 100

    # WHEN calculating the average quality score
    average_quality_score: float = calculate_average_quality_score_for_sample_in_lane(
        demux_result=conversion_result.demux_results[0]
    )

    # THEN the average quality score should be the sum of the quality scores for all reads in the sample
    # divided by  the total yield for the sample
    assert average_quality_score == 1.0


def test_calculate_q30_ratio(conversion_result: ConversionResult):
    """Test calculating the q30 ratio from a conversion result."""
    # GIVEN a conversion result with a known q30 ratio
    for read in conversion_result.demux_results[0].read_metrics:
        read.yield_q30 = 100
        read.yield_ = 100

    # WHEN calculating the q30 ratio
    q30_ratio: float = calculate_q30_ratio_for_sample_in_lane(
        demux_result=conversion_result.demux_results[0]
    )

    # THEN the q30 ratio should be the sum of the q30 bases for all reads in the sample
    # divided by the total yield for the sample
    assert q30_ratio == 1.0
