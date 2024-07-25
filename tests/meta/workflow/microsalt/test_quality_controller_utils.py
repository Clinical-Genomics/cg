from cg.constants.constants import MicrosaltAppTags
from cg.meta.workflow.microsalt.metrics_parser.models import SampleMetrics
from cg.meta.workflow.microsalt.quality_controller.models import SampleQualityResult
from cg.meta.workflow.microsalt.quality_controller.utils import (
    get_non_urgent_results,
    get_urgent_results,
    has_valid_10x_coverage,
    has_valid_average_coverage,
    has_valid_duplication_rate,
    has_valid_mapping_rate,
    has_valid_median_insert_size,
    is_valid_10x_coverage,
    is_valid_average_coverage,
    is_valid_duplication_rate,
    is_valid_mapping_rate,
    is_valid_median_insert_size,
    is_valid_total_reads,
    is_valid_total_reads_for_negative_control,
    negative_control_pass_qc,
    non_urgent_samples_pass_qc,
    urgent_samples_pass_qc,
)
from tests.meta.workflow.microsalt.conftest import create_quality_result, create_sample_metrics


def test_sample_total_reads_passing():
    # GIVEN sufficient reads
    sample_reads = 100
    target_reads = 100

    # WHEN checking if the sample has sufficient reads
    passes_reads_threshold: bool = is_valid_total_reads(
        reads=sample_reads, target_reads=target_reads, threshold_percentage=90
    )

    # THEN it passes
    assert passes_reads_threshold


def test_sample_total_reads_failing():
    # GIVEN insufficient reads
    sample_reads = 50
    target_reads = 100

    # WHEN checking if the sample has sufficient reads
    passes_reads_threshold: bool = is_valid_total_reads(
        reads=sample_reads, target_reads=target_reads, threshold_percentage=90
    )

    # THEN it fails
    assert not passes_reads_threshold


def test_sample_total_reads_failing_without_reads():
    # GIVENout reads
    sample_reads = 0
    target_reads = 100

    # WHEN checking if the sample has sufficient reads
    passes_reads_threshold: bool = is_valid_total_reads(
        reads=sample_reads, target_reads=target_reads, threshold_percentage=90
    )

    # THEN it fails
    assert not passes_reads_threshold


def test_control_total_reads_passing():
    # GIVEN a negative control sample with few reads
    sample_reads = 1
    target_reads = 100

    # WHEN checking if the control read count is valid
    passes_reads_threshold: bool = is_valid_total_reads_for_negative_control(
        reads=sample_reads, target_reads=target_reads
    )

    # THEN it passes
    assert passes_reads_threshold


def test_control_total_reads_failing():
    # GIVEN a negative control sample with many reads
    sample_reads = 100
    target_reads = 100

    # WHEN checking if the control read count is valid
    passes_reads_threshold: bool = is_valid_total_reads_for_negative_control(
        reads=sample_reads, target_reads=target_reads
    )

    # THEN it fails
    assert not passes_reads_threshold


def test_control_total_reads_passing_without_reads():
    # GIVEN a negative control sample without reads
    sample_reads = 0
    target_reads = 100

    # WHEN checking if the control read count is valid
    passes_reads_threshold: bool = is_valid_total_reads_for_negative_control(
        reads=sample_reads, target_reads=target_reads
    )

    # THEN it passes
    assert passes_reads_threshold


def test_is_valid_mapping_rate_passing():
    # GIVEN a high mapping rate
    mapping_rate = 0.99

    # WHEN checking if the mapping rate is valid
    passes_mapping_rate_threshold: bool = is_valid_mapping_rate(mapping_rate)

    # THEN it passes
    assert passes_mapping_rate_threshold


def test_is_valid_mapping_rate_failing():
    # GIVEN a low mapping rate
    mapping_rate = 0.1

    # WHEN checking if the mapping rate is valid
    passes_mapping_rate_threshold: bool = is_valid_mapping_rate(mapping_rate)

    # THEN it fails
    assert not passes_mapping_rate_threshold


def test_is_valid_duplication_rate_passing():
    # GIVEN a low duplication rate
    duplication_rate = 0.1

    # WHEN checking if the duplication rate is valid
    passes_duplication_qc: bool = is_valid_duplication_rate(duplication_rate)

    # THEN it passes
    assert passes_duplication_qc


def test_is_valid_duplication_rate_failing():
    # GIVEN a high duplication rate
    duplication_rate = 0.9

    # WHEN checking if the duplication rate is valid
    passes_duplication_qc: bool = is_valid_duplication_rate(duplication_rate)

    # THEN it fails
    assert not passes_duplication_qc


def test_is_valid_median_insert_size_passing():
    # GIVEN a high median insert size
    insert_size = 1000

    # WHEN checking if the median insert size is valid
    passes_insert_size_qc: bool = is_valid_median_insert_size(insert_size)

    # THEN it passes
    assert passes_insert_size_qc


def test_is_valid_median_insert_size_failing():
    # GIVEN a low median insert size
    insert_size = 10

    # WHEN checking if the median insert size is valid
    passes_insert_size_qc = is_valid_median_insert_size(insert_size)

    # THEN it fails
    assert not passes_insert_size_qc


def test_is_valid_average_coverage_passing():
    # GIVEN a high average coverage
    average_coverage = 50

    # WHEN checking if the average coverage is valid
    passes_average_coverage_qc: bool = is_valid_average_coverage(average_coverage)

    # THEN it passes
    assert passes_average_coverage_qc


def test_is_valid_average_coverage_failing():
    # GIVEN a low average coverage
    average_coverage = 1

    # WHEN checking if the average coverage is valid
    passes_average_coverage_qc: bool = is_valid_average_coverage(average_coverage)

    # THEN it fails
    assert not passes_average_coverage_qc


def test_is_valid_10x_coverage_passing():
    # GIVEN a high percent of bases covered at 10x
    coverage_10x = 0.95

    # WHEN checking if the coverage is valid
    passes_coverage_10x_qc: bool = is_valid_10x_coverage(coverage_10x)

    # THEN it passes
    assert passes_coverage_10x_qc


def test_is_valid_10x_coverage_failing():
    # GIVEN a low percent of bases covered at 10x
    coverage_10x = 0.1

    # WHEN checking if the coverage is valid
    passes_coverage_10x_qc: bool = is_valid_10x_coverage(coverage_10x)

    # THEN it fails
    assert not passes_coverage_10x_qc


def test_has_valid_mapping_rate_passing():
    # GIVEN metrics with a high mapping rate
    metrics: SampleMetrics = create_sample_metrics(mapped_rate=0.8)

    # WHEN checking if the mapping rate is valid
    passes_mapping_rate_qc: bool = has_valid_mapping_rate(metrics)

    # THEN it passes the quality control
    assert passes_mapping_rate_qc


def test_has_valid_mapping_rate_missing():
    # GIVEN metrics without a mapping rate
    metrics: SampleMetrics = create_sample_metrics(mapped_rate=None)

    # WHEN checking if the mapping rate is valid
    passes_mapping_rate_qc: bool = has_valid_mapping_rate(metrics)

    # THEN it fails the quality control
    assert not passes_mapping_rate_qc


def test_has_valid_duplication_rate_passing():
    # GIVEN metrics with a low duplication rate
    metrics: SampleMetrics = create_sample_metrics(duplication_rate=0.1)

    # WHEN checking if the duplication rate is valid
    passes_duplication_rate_qc: bool = has_valid_duplication_rate(metrics)

    # THEN it passes the quality control
    assert passes_duplication_rate_qc


def test_has_valid_duplication_rate_missing():
    # GIVEN metrics without a duplication rate
    metrics: SampleMetrics = create_sample_metrics(duplication_rate=None)

    # WHEN checking if the duplication rate is valid
    passes_duplication_rate_qc: bool = has_valid_duplication_rate(metrics)

    # THEN it fails the quality control
    assert not passes_duplication_rate_qc


def test_has_valid_median_insert_size_passing():
    # GIVEN metrics with a high median insert size
    metrics: SampleMetrics = create_sample_metrics(insert_size=200)

    # WHEN checking if the median insert size is valid
    passes_insert_size_qc: bool = has_valid_median_insert_size(metrics)

    # THEN it passes the quality control
    assert passes_insert_size_qc


def test_has_valid_median_insert_size_missing():
    # GIVEN metrics without a median insert size
    metrics: SampleMetrics = create_sample_metrics(insert_size=None)

    # WHEN checking if the median insert size is valid
    passes_insert_size_qc: bool = has_valid_median_insert_size(metrics)

    # THEN it fails the quality control
    assert not passes_insert_size_qc


def test_has_valid_average_coverage_passes():
    # GIVEN metrics with a high average coverage
    metrics: SampleMetrics = create_sample_metrics(average_coverage=30.0)

    # WHEN checking if the average coverage is valid
    passes_average_coverage_qc: bool = has_valid_average_coverage(metrics)

    # THEN it passes the quality control
    assert passes_average_coverage_qc


def test_has_valid_average_coverage_missing():
    # GIVEN metrics without an average coverage
    metrics: SampleMetrics = create_sample_metrics(average_coverage=None)

    # WHEN checking if the average coverage is valid
    passes_average_coverage_qc: bool = has_valid_average_coverage(metrics)

    # THEN it fails the quality control
    assert not passes_average_coverage_qc


def test_has_valid_10x_coverage_passing():
    # GIVEN metrics with a high percent of bases covered at 10x
    metrics: SampleMetrics = create_sample_metrics(coverage_10x=95.0)

    # WHEN checking if the coverage is valid
    passes_coverage_10x_qc: bool = has_valid_10x_coverage(metrics)

    # THEN it passes the quality control
    assert passes_coverage_10x_qc


def test_has_valid_10x_coverage_missing():
    # GIVEN metrics without a percent of bases covered at 10x
    metrics: SampleMetrics = create_sample_metrics(coverage_10x=None)

    # WHEN checking if the coverage is valid
    passes_coverage_10x_qc: bool = has_valid_10x_coverage(metrics)

    # THEN it fails the quality control
    assert not passes_coverage_10x_qc


def test_negative_control_passes_qc():
    # GIVEN a negative control sample that passes quality control
    control_result: SampleQualityResult = create_quality_result(is_control=True)
    other_result: SampleQualityResult = create_quality_result(passes_qc=False)

    # WHEN checking if the negative control passes quality control
    control_passes_qc: bool = negative_control_pass_qc([other_result, control_result])

    # THEN it passes quality control
    assert control_passes_qc


def test_negative_control_fails_qc():
    # GIVEN a negative control sample that fails quality control
    control_result: SampleQualityResult = create_quality_result(is_control=True, passes_qc=False)
    other_result: SampleQualityResult = create_quality_result()

    # WHEN checking if the negative control passes quality control
    control_passes_qc: bool = negative_control_pass_qc([other_result, control_result])

    # THEN it fails quality control
    assert not control_passes_qc


def test_get_urgent_results():
    # GIVEN quality results with urgent and non-urgent samples
    urgent_result: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWRNXTR003, passes_qc=True
    )
    non_urgent_result: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWXNXTR003, passes_qc=True
    )
    quality_results: list[SampleQualityResult] = [urgent_result, non_urgent_result]

    # WHEN getting the urgent results
    urgent_results: list[SampleQualityResult] = get_urgent_results(quality_results)

    # THEN the urgent results are returned
    assert urgent_results == [urgent_result]


def test_urgent_samples_pass_qc():
    # GIVEN quality results with urgent samples that pass quality control
    urgent_result: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWRNXTR003, passes_qc=True
    )
    urgent_result_control: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWRNXTR003, passes_qc=True, is_control=True
    )
    urgent_results: list[SampleQualityResult] = [urgent_result, urgent_result_control]

    # WHEN checking if the urgent samples pass quality control
    urgent_pass_qc: bool = urgent_samples_pass_qc(urgent_results)

    # THEN it passes quality control
    assert urgent_pass_qc


def test_urgent_samples_fail_qc():
    # GIVEN quality results with urgent samples that fail quality control
    urgent_result: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWRNXTR003, passes_qc=False
    )
    urgent_result_control: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWRNXTR003, passes_qc=True, is_control=True
    )
    urgent_results: list[SampleQualityResult] = [urgent_result, urgent_result_control]

    # WHEN checking if the urgent samples pass quality control
    urgent_pass_qc: bool = urgent_samples_pass_qc(urgent_results)

    # THEN it fails quality control
    assert not urgent_pass_qc


def test_get_non_urgent_results():
    # GIVEN quality results with urgent and non-urgent samples
    urgent_result: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWRNXTR003, passes_qc=True
    )
    non_urgent_result: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWXNXTR003, passes_qc=True
    )
    quality_results: list[SampleQualityResult] = [urgent_result, non_urgent_result]

    # WHEN getting the non-urgent results
    non_urgent_results: list[SampleQualityResult] = get_non_urgent_results(quality_results)

    # THEN the non-urgent results are returned
    assert non_urgent_results == [non_urgent_result]


def test_non_urgent_samples_pass_qc():
    # GIVEN quality results with non-urgent samples that pass quality control
    non_urgent_result: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWXNXTR003, passes_qc=True
    )
    non_urgent_result_control: SampleQualityResult = create_quality_result(
        application_tag=MicrosaltAppTags.MWXNXTR003, passes_qc=True, is_control=True
    )
    non_urgent_results: list[SampleQualityResult] = [non_urgent_result, non_urgent_result_control]

    # WHEN checking if the non-urgent samples pass quality control
    non_urgent_pass_qc: bool = non_urgent_samples_pass_qc(non_urgent_results)

    # THEN it passes quality control
    assert non_urgent_pass_qc
