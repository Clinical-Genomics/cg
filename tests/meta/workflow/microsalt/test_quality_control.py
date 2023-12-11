import pytest

from cg.constants.constants import MicrosaltQC
from cg.meta.workflow.microsalt.utils import is_total_reads_above_failure_threshold

TARGET_READS_FAIL_THRESHOLD = MicrosaltQC.TARGET_READS_FAIL_THRESHOLD

test_cases = [
    (TARGET_READS_FAIL_THRESHOLD * 100, 100, False, "sufficient_reads"),
    (TARGET_READS_FAIL_THRESHOLD * 100 - 1, 100, True, "just_below_threshold"),
    (0, 100, True, "edge_case_no_reads"),
    (TARGET_READS_FAIL_THRESHOLD * 100, 0, False, "edge_case_no_target_reads"),
]


@pytest.mark.parametrize(
    "sample_reads, target_reads, expected_result, test_id", test_cases, ids=lambda x: x[-1]
)
def test_is_total_reads_above_failure_threshold(
    sample_reads, target_reads, expected_result, test_id
):
    # GIVEN a sample with a number of reads and a target number of reads

    # WHEN checking if the sample has sufficient reads
    result = is_total_reads_above_failure_threshold(
        sample_reads=sample_reads, target_reads=target_reads
    )

    # THEN the result should be as expected
    assert result == expected_result, f"Test failed for {test_id}"
