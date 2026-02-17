from datetime import datetime
from unittest.mock import create_autospec

import pytest

from cg.constants.devices import DeviceType
from cg.constants.priority import Priority
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import ApplicationDoesNotHaveHiFiYieldError
from cg.services.sequencing_qc_service.quality_checks.utils import (
    any_sample_in_case_has_reads,
    case_pass_sequencing_qc_on_hifi_yield,
    case_pass_sequencing_qc_on_reads,
    express_case_pass_sequencing_qc_on_reads,
    express_sample_has_enough_reads,
    get_express_reads_threshold_for_sample,
    is_case_express_priority,
    is_sample_express_priority,
    is_sample_ready_made_library,
    raw_data_case_pass_qc,
    ready_made_library_sample_has_enough_reads,
    sample_has_enough_reads,
)
from cg.store.models import Application, ApplicationVersion, Case, Sample, SampleRunMetrics
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


def test_case_pass_sequencing_qc_on_reads_express_delivered_at_pass():
    # GIVEN a case with express priority and less than half the target reads
    # GIVEN that the sample has a delivered at date
    past_date: datetime = datetime(2026, 2, 16, 0, 0, 0)
    sample: Sample = create_autospec(
        Sample,
        delivered_at=past_date,
        reads=9,
        application_version=create_autospec(
            ApplicationVersion,
            application=create_autospec(
                Application,
                target_reads=20,
            ),
        ),
    )
    case: Case = create_autospec(Case, samples=[sample], priority=Priority.express)

    # WHEN calling case_pass_sequencing_qc_on_reads on the case
    passes: bool = case_pass_sequencing_qc_on_reads(case)

    # THEN the case does pass sequencing qc
    assert passes


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

    assert case_pass_sequencing_qc_on_reads(case) == expected_result


def test_case_pass_sequencing_qc_on_reads_delivered_at_pass():
    # GIVEN a sample with a delivered at data with less than enough amount of reads
    past_date: datetime = datetime(2026, 2, 16, 0, 0, 0)
    sample: Sample = create_autospec(
        Sample,
        delivered_at=past_date,
        reads=10,
        expected_reads_for_sample=20,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.ILLUMINA)],
    )

    # GIVEN a case
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling the case_pass_sequencing_qc_on_reads function on the case
    passes = case_pass_sequencing_qc_on_reads(case)

    # THEN the case pass QC
    assert passes


def test_case_pass_sequencing_qc_on_reads_delivered_at_mixed_case_pass():
    # GIVEN a sample with a delivered at data with less than enough amount of reads
    past_date: datetime = datetime(2026, 2, 16, 0, 0, 0)
    sample_1: Sample = create_autospec(
        Sample,
        delivered_at=past_date,
        reads=10,
        expected_reads_for_sample=20,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.ILLUMINA)],
    )

    # GIVEN a sample with no delivered_at date but enough of reads
    sample_2: Sample = create_autospec(
        Sample,
        delivered_at=None,
        reads=20,
        expected_reads_for_sample=20,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.ILLUMINA)],
    )

    # GIVEN a case
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])

    # WHEN calling the case_pass_sequencing_qc_on_reads function on the case
    passes = case_pass_sequencing_qc_on_reads(case)

    # THEN the case pass QC
    assert passes


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
    express_sequencing_qc_of_case: bool = express_case_pass_sequencing_qc_on_reads(case)
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
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        pass_sequencing_qc=False,
        priority=case.priority,
    )
    helpers.add_relationship(store=base_store, sample=another_sample, case=case)
    # WHEN checking if any sample in the case has reads
    any_sample_in_case_has_reads_result: bool = any_sample_in_case_has_reads(case)
    # THEN the result should be as expected
    assert any_sample_in_case_has_reads_result == expected_result


def test_case_pass_sequencing_qc_on_hifi_yield_passes():
    # GIVEN a sample with enough yield
    sample: Sample = create_autospec(Sample, expected_hifi_yield=45, hifi_yield=45)

    # GIVEN a case
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling case_pass_sequencing_qc_on_hifi_yield on the case
    passes: bool = case_pass_sequencing_qc_on_hifi_yield(case)

    # THEN the case passes sequencing qc
    assert passes


def test_case_pass_sequencing_qc_on_hifi_yield_delivered_at_pass():
    # GIVEN a sample with a delivered at data with less than enough amount of reads:
    past_date: datetime = datetime(2026, 2, 16, 0, 0, 0)
    sample: Sample = create_autospec(
        Sample,
        delivered_at=past_date,
        hifi_yield=10,
        expected_hifi_yield=20,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.PACBIO)],
    )

    # GIVEN a case
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling the case_pass_sequencing_qc_on_hifi_yield function on the case
    passes = case_pass_sequencing_qc_on_hifi_yield(case)

    # THEN the case fails QC
    assert passes


def test_case_pass_sequencing_qc_on_hifi_yield_delivered_at_mixed_case_pass():
    # GIVEN a sample with a delivered at data with less than enough amount of reads:
    past_date: datetime = datetime(2026, 2, 16, 0, 0, 0)
    sample_1: Sample = create_autospec(
        Sample,
        delivered_at=past_date,
        hifi_yield=10,
        expected_hifi_yield=20,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.PACBIO)],
    )
    # GIVEN a sample with no delivered_at but enough HiFi yield
    sample_2: Sample = create_autospec(
        Sample,
        delivered_at=None,
        hifi_yield=20,
        expected_hifi_yield=20,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.PACBIO)],
    )

    # GIVEN a case
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])

    # WHEN calling the case_pass_sequencing_qc_on_hifi_yield function on the case
    passes = case_pass_sequencing_qc_on_hifi_yield(case)

    # THEN the case passes QC
    assert passes


def test_case_pass_sequencing_qc_on_hifi_yield_fails():
    # GIVEN a sample without enough yield
    sample: Sample = create_autospec(
        Sample, delivered_at=None, expected_hifi_yield=45, hifi_yield=44
    )

    # GIVEN a case
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling case_pass_sequencing_qc_on_hifi_yield on the case
    passes: bool = case_pass_sequencing_qc_on_hifi_yield(case)

    # THEN the case passes sequencing qc
    assert not passes


def test_case_pass_sequencing_qc_on_hifi_yield_missing_hifi_yield():
    # GIVEN a case with two samples, where one is missing HiFi yield
    sample_with_yield: Sample = create_autospec(
        Sample, delivered_at=None, hifi_yield=45, expected_hifi_yield=45
    )
    sample_without_yield: Sample = create_autospec(
        Sample,
        delivered_at=None,
        hifi_yield=None,
        expected_hifi_yield=45,
    )

    # GIVEN a case with the two samples above
    case: Case = create_autospec(Case, samples=[sample_with_yield, sample_without_yield])

    # WHEN calling case_pass_sequencing_qc_on_hifi_yield on the case
    passes: bool = case_pass_sequencing_qc_on_hifi_yield(case)

    # THEN the case does not pass sequencing qc
    assert sample_with_yield.delivered_at is None
    assert sample_without_yield.delivered_at is None
    assert not passes


def test_case_pass_sequencing_qc_on_hifi_yield_wrong_application():
    # GIVEN a case with an application without target HiFi yield
    sample: Sample = create_autospec(Sample, hifi_yield=25, expected_hifi_yield=None)
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling the case_pass_sequencing_qc_on_hifi_yield on the case
    # THEN an error is raised
    with pytest.raises(ApplicationDoesNotHaveHiFiYieldError):
        case_pass_sequencing_qc_on_hifi_yield(case)


def test_case_pass_sequencing_qc_on_hifi_yield_express_wrong_application():
    # GIVEN a case with an application without target HiFi yield
    sample: Sample = create_autospec(Sample, hifi_yield=25, expected_hifi_yield=None)
    case: Case = create_autospec(Case, samples=[sample], priority=Priority.express)

    # WHEN calling the case_pass_sequencing_qc_on_hifi_yield on the case
    # THEN an error is raised
    with pytest.raises(ApplicationDoesNotHaveHiFiYieldError):
        case_pass_sequencing_qc_on_hifi_yield(case)


def test_case_pass_sequencing_qc_on_hifi_yield_express_priority_passes():
    # GIVEN a case with a PacBio application, express priority and half of the target yield
    sample: Sample = create_autospec(
        Sample,
        hifi_yield=25,
        application_version=create_autospec(
            ApplicationVersion,
            application=create_autospec(Application, expected_express_hifi_yield=25),
        ),
    )
    case: Case = create_autospec(Case, samples=[sample], priority=Priority.express)

    # WHEN calling case_pass_sequencing_qc_on_hifi_yield on the case
    passes: bool = case_pass_sequencing_qc_on_hifi_yield(case)

    # THEN the case passes sequencing qc
    assert passes


def test_case_pass_sequencing_qc_on_hifi_yield_express_priority_fails():
    # GIVEN a case with a PacBio application, express priority and less than half the target yield
    sample: Sample = create_autospec(
        Sample,
        delivered_at=None,
        hifi_yield=24,
        application_version=create_autospec(
            ApplicationVersion,
            application=create_autospec(Application, expected_express_hifi_yield=25),
        ),
    )
    case: Case = create_autospec(Case, samples=[sample], priority=Priority.express)

    # WHEN calling case_pass_sequencing_qc_on_hifi_yield on the case
    passes: bool = case_pass_sequencing_qc_on_hifi_yield(case)

    # THEN the case does not pass sequencing qc
    assert sample.delivered_at is None
    assert not passes


def test_case_pass_sequencing_qc_on_hifi_yield_express_priority_delivered_at_pass():
    # GIVEN a case with a PacBio application, express priority and less than half the target yield
    # GIVEN that the sample has a delivered at date
    past_date: datetime = datetime(2026, 2, 16, 0, 0, 0)
    sample: Sample = create_autospec(
        Sample,
        delivered_at=past_date,
        hifi_yield=24,
        application_version=create_autospec(
            ApplicationVersion,
            application=create_autospec(Application, expected_express_hifi_yield=25),
        ),
    )
    case: Case = create_autospec(Case, samples=[sample], priority=Priority.express)

    # WHEN calling case_pass_sequencing_qc_on_hifi_yield on the case
    passes: bool = case_pass_sequencing_qc_on_hifi_yield(case)

    # THEN the case does pass sequencing qc
    assert sample.delivered_at is past_date
    assert passes


def test_case_pass_sequencing_qc_on_hifi_yield_express_priority_missing_hifi_yield():
    # GIVEN two PacBio samples, were one is missing HiFi yield
    application_version = create_autospec(
        ApplicationVersion,
        application=create_autospec(Application, expected_express_hifi_yield=25),
    )
    sample_with_yield: Sample = create_autospec(
        Sample, hifi_yield=24, application_version=application_version
    )
    sample_without_yield: Sample = create_autospec(
        Sample,
        hifi_yield=None,
        application_version=application_version,
    )

    # GIVEN a case with a PacBio application express priority, with the two sample above
    case: Case = create_autospec(
        Case, samples=[sample_with_yield, sample_without_yield], priority=Priority.express
    )

    # WHEN calling case_pass_sequencing_qc_on_hifi_yield on the case
    passes: bool = case_pass_sequencing_qc_on_hifi_yield(case)

    # THEN the case does not pass sequencing qc
    assert not passes


def test_case_pass_sequencing_qc_on_hifi_yield_express_priority_wrong_application():
    # GIVEN an express priority case with an application without expected express HiFi yield
    # because of a missing target_hifi_yield
    sample: Sample = create_autospec(
        Sample,
        hifi_yield=25,
        application_version=create_autospec(
            ApplicationVersion,
            application=create_autospec(Application, expected_express_hifi_yield=None),
        ),
    )
    case: Case = create_autospec(Case, samples=[sample], priority=Priority.express)

    # WHEN calling the case_pass_sequencing_qc_on_hifi_yield on the case
    # THEN an error is raised
    with pytest.raises(ApplicationDoesNotHaveHiFiYieldError):
        case_pass_sequencing_qc_on_hifi_yield(case)


def test_raw_data_case_pass_qc_rml_passes():
    # GIVEN two RML samples for which their summed reads pass the application threshold
    sample_1: Sample = create_autospec(
        Sample,
        reads=10,
        expected_reads_for_sample=20,
        prep_category=SeqLibraryPrepCategory.READY_MADE_LIBRARY,
    )
    sample_2: Sample = create_autospec(
        Sample,
        reads=10,
        expected_reads_for_sample=20,
        prep_category=SeqLibraryPrepCategory.READY_MADE_LIBRARY,
    )

    # GIVEN a case with the RML samples
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])

    # WHEN calling the raw_data_case_pass_qc function on the case
    passes = raw_data_case_pass_qc(case)

    # THEN the case passes QC
    assert passes


def test_raw_data_case_pass_qc_rml_fails():
    # GIVEN two RML samples for which their summed reads does not reach the application threshold
    sample_1: Sample = create_autospec(
        Sample,
        reads=1,
        expected_reads_for_sample=20,
        prep_category=SeqLibraryPrepCategory.READY_MADE_LIBRARY,
    )
    sample_2: Sample = create_autospec(
        Sample,
        reads=1,
        expected_reads_for_sample=20,
        prep_category=SeqLibraryPrepCategory.READY_MADE_LIBRARY,
    )

    # GIVEN a case with the RML samples
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])

    # WHEN calling the raw_data_case_pass_qc function on the case
    passes = raw_data_case_pass_qc(case)

    # THEN the case fails QC
    assert not passes


def test_raw_data_case_pass_qc_read_based_not_rml_passes():
    # GIVEN a raw-data non rml sample with enough reads
    sample: Sample = create_autospec(
        Sample,
        reads=10,
        expected_reads_for_sample=10,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.ILLUMINA)],
    )

    # GIVEN a case with the sample above
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling the raw_data_case_pass_qc function on the case
    passes = raw_data_case_pass_qc(case)

    # THEN the case passes QC
    assert passes


def test_raw_data_case_pass_qc_read_based_not_rml_fails():
    # GIVEN a raw-data non rml sample without enough reads
    sample: Sample = create_autospec(
        Sample,
        delivered_at=None,
        reads=10,
        expected_reads_for_sample=20,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.ILLUMINA)],
    )

    # GIVEN a case with the sample above
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling the raw_data_case_pass_qc function on the case
    passes = raw_data_case_pass_qc(case)

    # THEN the case fails QC
    assert not passes


def test_raw_data_case_pass_qc_hifi_yield_based_passes():
    # GIVEN a raw-data yield based sample with enough HiFi yield
    sample: Sample = create_autospec(
        Sample,
        hifi_yield=10,
        expected_hifi_yield=10,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.PACBIO)],
    )

    # GIVEN a case with the sample above
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling the raw_data_case_pass_qc function on the case
    passes = raw_data_case_pass_qc(case)

    # THEN the case passes QC
    assert passes


def test_raw_data_case_pass_qc_hifi_yield_based_fails():
    # GIVEN a raw-data yield based sample without enough HiFi yield
    sample: Sample = create_autospec(
        Sample,
        delivered_at=None,
        hifi_yield=10,
        expected_hifi_yield=20,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.PACBIO)],
    )

    # GIVEN a case with the sample above
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling the raw_data_case_pass_qc function on the case
    passes = raw_data_case_pass_qc(case)

    # THEN the case fails QC
    assert sample.delivered_at is None
    assert not passes


def test_raw_data_case_pass_qc_sample_run_metrics_missing():
    # GIVEN a raw-data sample without sample run metrics
    sample: Sample = create_autospec(Sample, sample_run_metrics=[])

    # GIVEN a case with the sample above
    case: Case = create_autospec(Case, samples=[sample])

    # WHEN calling the raw_data_case_pass_qc function on the case
    passes = raw_data_case_pass_qc(case)

    # THEN the case fails QC
    assert not passes


def test_raw_data_yield_based_case_pass_qc_second_sample_missing_sample_run_metrics():
    # GIVEN two raw-data samples, the second sample is missing sample_run_metrics
    sample_1: Sample = create_autospec(
        Sample,
        hifi_yield=10,
        expected_hifi_yield=10,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.PACBIO)],
    )
    sample_2: Sample = create_autospec(
        Sample, hifi_yield=None, expected_hifi_yield=10, sample_run_metrics=[]
    )

    # GIVEN a case with the samples above
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])

    # WHEN calling the raw_data_case_pass_qc function on the case
    passes = raw_data_case_pass_qc(case)

    # THEN the case fails QC
    assert not passes


def test_raw_data_read_based_case_pass_qc_second_sample_missing_sample_run_metrics():
    # GIVEN two raw-data samples, the second sample is missing sample_run_metrics
    sample_1: Sample = create_autospec(
        Sample,
        delivered_at=None,
        reads=10,
        expected_reads_for_sample=10,
        sample_run_metrics=[create_autospec(SampleRunMetrics, type=DeviceType.ILLUMINA)],
    )
    sample_2: Sample = create_autospec(
        Sample, delivered_at=None, reads=0, expected_reads_for_sample=10, sample_run_metrics=[]
    )

    # GIVEN a case with the samples above
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])

    # WHEN calling the raw_data_case_pass_qc function on the case
    passes = raw_data_case_pass_qc(case)

    # THEN the case fails QC
    assert not passes
