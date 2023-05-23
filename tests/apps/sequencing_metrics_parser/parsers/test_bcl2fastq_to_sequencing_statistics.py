from typing import List
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq_to_sequencing_statistics import (
    calculate_pass_filter_ratio,
    calculate_yield_in_megabases,
)
from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import ConversionResult, DemuxResult


def test_calculate_pass_ratio_from_conversion_result(
    conversion_result: ConversionResult,
):
    # GIVEN a conversion result with valid total clusters
    # WHEN calculating the pass filter ratio
    pass_filter_ratio: float = calculate_pass_filter_ratio(conversion_result=conversion_result)

    # THEN the pass filter ratio should be the the clusters passing the filter divided by the total clusters
    correct_filter_ratio: float = (
        conversion_result.total_clusters_pf / conversion_result.total_clusters_raw
    )

    assert pass_filter_ratio == correct_filter_ratio


def test_calculate_yield_in_megabases_from_conversion_result(conversion_result: ConversionResult):
    # GIVEN a conversion result with a known yield
    for demux_result in conversion_result.demux_results:
        demux_result.yield_ = 1000000

    # WHEN calculating the yield in megabases
    yield_in_megabases: int = calculate_yield_in_megabases(conversion_result=conversion_result)

    # THEN the yield in megabases should be the sum of the yields for all samples in the lane divided by 1 million
    assert yield_in_megabases == len(conversion_result.demux_results)


def test_calculate_average_quality_score():
    pass
