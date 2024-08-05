import pytest
from cg.store.models import Case, Sample
from cg.constants.constants import PrepCategory
from cg.services.sequencing_qc_service.quality_checks.utils import (
    any_sample_in_case_has_reads,
    is_case_express_priority,
    case_pass_sequencing_qc,
    express_case_pass_sequencing_qc,
    express_sample_has_enough_reads,
    get_express_reads_threshold_for_sample,
    is_sample_ready_made_library,
    is_sample_express_priority,
    ready_made_library_sample_has_enough_reads,
    sample_has_enough_reads,
)
from cg.store.store import Store
from tests.conftest import StoreHelpers
from tests.fixture_plugins.quality_controller_fixtures.sequencing_qc_check_scenario import (
    SequencingQCCheckScenarios,
)


@pytest.mark.parametrize(
    "sample_fixture, expected_result",
    [
        ("ready_made_library_sample_passing_sequencing_qc", True),
        ("sample_passing_sequencing_qc", False),
    ],
    ids=["ready_made_library", "whole_genome_sequencing"],
)
def test_is_sample_ready_made_library(
    sample_fixture: str, expected_result: bool, request: pytest.FixtureRequest
):
    """
    Test the is_sample_ready_made_library function.

    This test verifies if the sample is ready-made library based on its prep category.
    """
    # GIVEN a sample with a prep category
    sample: Sample = request.getfixturevalue(sample_fixture)
    # WHEN checking if the sample is a ready-made library
    # THEN the result should be as expected

    assert is_sample_ready_made_library(sample) == expected_result


@pytest.mark.parametrize(
    "case_fixture, expected_result",
    [
        ("express_case_passing_sequencing_qc", True),
        ("case_passing_sequencing_qc", False),
    ],
    ids=["express_priority", "standard_priority"],
)
def test_is_case_express_priority(
    case_fixture: str, expected_result: bool, request: pytest.FixtureRequest
):
    """
    Test the is_case_express_priority function.

    This test verifies if the case has express priority.
    """
    # GIVEN a case with a priority
    case: Case = request.getfixturevalue(case_fixture)

    # WHEN checking if the case has express priority
    # THEN the result should be as expected
    assert is_case_express_priority(case) == expected_result


@pytest.mark.parametrize(
    "sample_fixture, expected_result",
    [
        ("express_sample_passing_sequencing_qc", True),
        ("sample_passing_sequencing_qc", False),
    ],
    ids=["express_priority", "standard_priority"],
)
def test_is_sample_express_priority(
    sample_fixture: str, expected_result: bool, request: pytest.FixtureRequest
):
    """
    Test the is_sample_express_priority function.

    This test verifies if the sample has express priority.
    """
    # GIVEN a sample with a priority
    sample: Sample = request.getfixturevalue(sample_fixture)

    # WHEN checking if the sample has express priority
    # THEN the result should be as expected

    assert is_sample_express_priority(sample) == expected_result


@pytest.mark.parametrize(
    "sample_fixture, expected_result",
    [
        ("ready_made_library_sample_passing_sequencing_qc", True),
        ("ready_made_library_sample_failing_sequencing_qc", False),
    ],
    ids=["pass_sequencing_qc", "no_reads"],
)
def test_ready_made_library_sample_has_enough_reads(
    sample_fixture: str,
    expected_result: bool,
    request: pytest.FixtureRequest,
):
    """
    Test the ready_made_library_sample_has_enough_reads function.

    This test verifies if the ready-made library sample has enough reads. It checks if the sample is a ready made
    library and if it has enough reads if so is the case.
    """
    # GIVEN a ready-made library sample with or without reads
    sample: Sample = request.getfixturevalue(sample_fixture)

    # WHEN checking if the ready-made library sample has enough reads
    # THEN the result should be as expected
    assert ready_made_library_sample_has_enough_reads(sample) == expected_result


@pytest.mark.parametrize(
    "sample_fixture, expected_result",
    [
        ("sample_passing_sequencing_qc", True),
        ("sample_failing_sequencing_qc", False),
    ],
    ids=["pass_sequencing_qc", "no_reads"],
)
def test_sample_has_enough_reads(
    sample_fixture: str, expected_result: bool, request: pytest.FixtureRequest
):
    """
    Test the sample_has_enough_reads function.

    This test verifies if the sample has enough reads. It checks if the sample has enough reads or not.
    """
    # GIVEN a sample with or without reads
    sample: Sample = request.getfixturevalue(sample_fixture)

    # WHEN checking if the sample has enough reads
    # THEN the result should be as expected
    assert sample_has_enough_reads(sample) == expected_result


@pytest.mark.parametrize(
    "case_fixture, expected_result",
    [
        ("case_passing_sequencing_qc", True),
        ("case_failing_sequencing_qc", False),
    ],
    ids=["standard_priority", "standard_priority_no_reads"],
)
def test_get_sequencing_qc_of_case(
    case_fixture: str, expected_result: bool, request: pytest.FixtureRequest
):
    """
    Test the get_sequencing_qc_of_case function.

    This test verifies the sequencing quality check of the case. It checks if the case has enough
    reads and if it has lower priority than express.

    """
    # GIVEN a case with standard priority and a sample
    case: Case = request.getfixturevalue(case_fixture)
    # WHEN getting the sequencing quality check of the case
    # THEN the sequencing quality check of the case should be as expected

    assert case_pass_sequencing_qc(case) == expected_result


@pytest.mark.parametrize(
    "sample_fixture, expected_result",
    [
        ("express_sample_passing_sequencing_qc", True),
        ("express_sample_failing_sequencing_qc", False),
    ],
    ids=["express_priority", "express_priority_no_reads"],
)
def test_express_sample_has_enough_reads(
    sample_fixture: str, expected_result: bool, request: pytest.FixtureRequest
):
    """
    Test the express_sample_has_enough_reads function.

    This test verifies the sequencing quality check of the express sample. It checks if the express sample has enough
    reads.

    """
    # GIVEN an express sample with or without reads
    sample: Sample = request.getfixturevalue(sample_fixture)
    # WHEN checking if the express sample has enough reads
    # THEN the result should be as expected

    assert express_sample_has_enough_reads(sample) == expected_result


def test_get_express_reads_threshold_for_sample(express_sample_passing_sequencing_qc: Sample):
    """
    Test the get_express_reads_threshold_for_sample function.

    This test verifies the express reads threshold is correctly calculated for a sample.
    """
    # GIVEN a sample with a target reads value of 10 and an expected threshold of 5
    express_sample_passing_sequencing_qc.application_version.application.target_reads = 10
    expected_express_reads_threshold = 5
    # WHEN getting the express reads threshold for the sample
    express_reads_threshold: int = get_express_reads_threshold_for_sample(
        express_sample_passing_sequencing_qc
    )
    # THEN the express reads threshold should be half of the target reads
    assert express_reads_threshold == expected_express_reads_threshold


@pytest.mark.parametrize(
    "case_fixture, expected_result",
    [
        ("express_case_passing_sequencing_qc", True),
        ("express_case_failing_sequencing_qc", False),
    ],
    ids=["express_priority", "express_priority_no_reads"],
)
def test_express_case_pass_sequencing_qc(
    case_fixture: str, expected_result: bool, request: pytest.FixtureRequest
):
    """
    Test the get_express_sequencing_qc_of_case function.

    This test verifies the express sequencing quality check of the case. It checks if the case has enough
    reads and if it has express priority.
    """

    # GIVEN a case with express priority and a sample
    case: Case = request.getfixturevalue(case_fixture)
    # WHEN getting the express sequencing quality check of the case
    express_sequencing_qc_of_case: bool = express_case_pass_sequencing_qc(case)
    # THEN the express sequencing quality check of the case should be as expected
    assert express_sequencing_qc_of_case == expected_result


@pytest.mark.parametrize(
    "case_fixture, expected_result",
    [
        ("one_sample_in_case_has_reads", True),
        ("no_sample_in_case_has_reads", False),
    ],
    ids=["one_sample_with_reads", "no_sample_with_reads"],
)
def test_any_sample_in_case_has_reads(
    case_fixture: str,
    expected_result: bool,
    request: pytest.FixtureRequest,
    sequencing_qc_check_scenarios: SequencingQCCheckScenarios,
    base_store: Store,
    helpers: StoreHelpers,
):
    """
    Test the any_sample_in_case_has_reads function.

    This test verifies if any sample in the case has reads.
    """
    # GIVEN a case with a sample with or without reads
    case: Case = request.getfixturevalue(case_fixture)
    # GIVEN that another sample on the case has no reads
    another_sample: Sample = sequencing_qc_check_scenarios.add_sample(
        prep_category=PrepCategory.WHOLE_EXOME_SEQUENCING,
        pass_sequencing_qc=False,
        priority=case.priority,
    )
    helpers.add_relationship(store=base_store, sample=another_sample, case=case)
    # WHEN checking if any sample in the case has reads
    any_sample_in_case_has_reads_result: bool = any_sample_in_case_has_reads(case)
    # THEN the result should be as expected
    assert any_sample_in_case_has_reads_result == expected_result
