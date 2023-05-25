from typing import List
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq_to_sequencing_statistics import (
    calculate_average_quality_score,
    calculate_pass_filter_ratio,
    calculate_perfect_reads_ratio,
    calculate_q30_ratio,
    calculate_yield_in_megabases,
)
from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import ConversionResult, DemuxResult


def test_calculate_pass_ratio_from_conversion_result(
    conversion_result: ConversionResult,
):
    """Test calculating the pass filter ratio from a conversion result."""
    # GIVEN a conversion result with valid total clusters

    # WHEN calculating the pass filter ratio
    pass_filter_ratio: float = calculate_pass_filter_ratio(conversion_result=conversion_result)

    # THEN the pass filter ratio should be the the clusters passing the filter divided by the total clusters
    correct_filter_ratio: float = (
        conversion_result.total_clusters_pf / conversion_result.total_clusters_raw
    )

    assert pass_filter_ratio == correct_filter_ratio


def test_calculate_yield_in_megabases_from_conversion_result(conversion_result: ConversionResult):
    """Test calculating the yield in megabases from a conversion result."""
    # GIVEN a conversion result with a known yield
    YIELD_IN_BASES = 1_000_000
    for demux_result in conversion_result.demux_results:
        demux_result.yield_ = YIELD_IN_BASES

    # WHEN calculating the yield in megabases
    yield_in_megabases: float = calculate_yield_in_megabases(conversion_result=conversion_result)

    # THEN the yield in megabases should be the sum of the yields for all samples in the lane divided by 1 million
    assert yield_in_megabases == len(conversion_result.demux_results)


def test_calculate_average_quality_score(conversion_result: ConversionResult):
    """ "Test calculating the average quality score from a conversion result."""
    # GIVEN a conversion result with a known average quality score
    for read in conversion_result.demux_results[0].read_metrics:
        read.quality_score_sum = 100
        read.yield_ = 100

    # WHEN calculating the average quality score
    average_quality_score: float = calculate_average_quality_score(
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
    q30_ratio: float = calculate_q30_ratio(demux_result=conversion_result.demux_results[0])

    # THEN the q30 ratio should be the sum of the q30 bases for all reads in the sample
    # divided by the total yield for the sample
    assert q30_ratio == 1.0


def test_calculate_perfect_reads_ratio(conversion_result: ConversionResult):
    """Test calculating the perfect reads ratio from a conversion result."""
    # GIVEN a conversion result with a known perfect reads ratio
    sample_demux_result: DemuxResult = conversion_result.demux_results[0]

    total_perfect_reads: int = 0
    for index_metric in sample_demux_result.index_metrics:
        total_perfect_reads += index_metric.mismatch_counts["0"]

    perfect_reads_ratio: float = total_perfect_reads / sample_demux_result.number_reads * 100

    # WHEN calculating the perfect reads ratio for the sample
    ratio: float = calculate_perfect_reads_ratio(demux_result=sample_demux_result)

    # THEN the perfect reads ratio should be the number of reads with 0 mismatches divided by the total number of reads
    # for the sample
    assert ratio == perfect_reads_ratio
