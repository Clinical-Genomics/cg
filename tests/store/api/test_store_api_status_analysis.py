"""This script tests the cli methods to add cases to status-db"""
from datetime import datetime, timedelta

from cg.constants import DataDelivery, Pipeline
from cg.store import Store


def test_that_many_cases_can_have_one_sample_each(base_store: Store, helpers):
    """Test that tests that cases are returned even if there are many result rows in the query"""

    # GIVEN a database with two cases one with 50 sequenced samples
    # the other case with one
    n_test_cases = 50
    test_cases = add_cases_with_samples(
        base_store, helpers, n_test_cases, sequenced_at=datetime.now()
    )

    # WHEN getting cases to analyse
    cases = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should contain the test case
    assert len(cases) == len(test_cases)


def test_that_cases_can_have_many_samples(base_store: Store, helpers):
    """Test that tests that cases are returned even if there are many result rows in the query"""

    # GIVEN a database with two cases one with 50 sequenced samples
    # the other case with one
    default_limit = 50
    test_case_50 = add_case_with_samples(
        base_store, helpers, "test_case_50åäp+ölo0l", default_limit, sequenced_at=datetime.now()
    )
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_case = helpers.add_case(base_store, "family_one_sample")
    base_store.relate_sample(test_case, test_sample, "unknown")

    # WHEN getting cases to analyse
    cases = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should contain the test case
    assert cases
    assert test_case_50 in cases
    assert test_case in cases


def test_external_sample_to_re_analyse(base_store: Store, helpers):
    """Test that a case marked for re-analyse with one sample external not sequenced inhouse and
    with completed analysis do show up among the cases to analyse"""

    # GIVEN a database with a case with one not sequenced external sample and completed analysis
    pipeline = Pipeline.MIP_DNA
    test_sample = helpers.add_sample(base_store, sequenced_at=None, is_external=True)
    test_analysis = helpers.add_analysis(base_store, completed_at=datetime.now(), pipeline=pipeline)
    test_analysis.family.action = "analyze"
    base_store.relate_sample(test_analysis.family, test_sample, "unknown")

    # WHEN getting cases to analyse
    cases = base_store.cases_to_analyze(pipeline=pipeline)

    # THEN cases should contain the test case
    assert cases
    assert test_analysis.family in cases


def test_case_to_re_analyse(base_store: Store, helpers):
    """Test that a case marked for re-analyse with one sample that has been sequenced and
    with completed analysis do show up among the cases to analyse"""

    # GIVEN a database with a case with one of one sequenced samples and completed analysis
    pipeline = Pipeline.MIP_DNA
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    assert test_sample.sequenced_at
    test_analysis = helpers.add_analysis(base_store, completed_at=datetime.now(), pipeline=pipeline)
    assert test_analysis.completed_at
    test_analysis.family.action = "analyze"
    assert test_analysis.family.action == "analyze"
    base_store.relate_sample(test_analysis.family, test_sample, "unknown")

    # WHEN getting cases to analyse
    cases = base_store.cases_to_analyze(pipeline=pipeline)

    # THEN cases should contain the test case
    assert cases
    assert test_analysis.family in cases


def test_all_samples_and_analysis_completed(base_store: Store, helpers):
    """Test that a case with one sample that has been sequenced and with completed
    analysis don't show up among the cases to analyse"""

    # GIVEN a database with a case with one of one sequenced samples and completed analysis
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_analysis = helpers.add_analysis(base_store, completed_at=datetime.now())
    test_analysis.family.action = "analyze"
    base_store.relate_sample(test_analysis.family, test_sample, "unknown")

    # WHEN getting cases to analyse
    cases = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should not contain the test case

    assert not cases


def test_specified_analysis_in_result(base_store: Store, helpers):
    """Test that a case with one sample that has specified data_analysis does show up"""

    # GIVEN a database with a case with one sequenced samples for MIP analysis
    pipeline = Pipeline.BALSAMIC
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_case = helpers.add_case(base_store, data_analysis=pipeline)
    base_store.relate_sample(test_case, test_sample, "unknown")

    # WHEN getting cases to analyse
    cases = base_store.cases_to_analyze(pipeline=pipeline)

    # THEN cases should contain the test case
    assert cases
    assert test_case in cases


def test_exclude_other_pipeline_analysis_from_result(base_store: Store, helpers):
    """Test that a case with specified analysis and with one sample does not show up among
    others"""

    # GIVEN a database with a case with one sequenced samples for specified analysis
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_case = helpers.add_case(base_store, data_analysis=Pipeline.BALSAMIC)
    base_store.relate_sample(test_case, test_sample, "unknown")

    # WHEN getting cases to analyse
    cases = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should not contain the test case
    assert not cases


def test_one_of_two_sequenced_samples(base_store: Store, helpers):
    """Test that a case with one of one samples that has been sequenced shows up among the
    cases to analyse"""

    # GIVEN a database with a case with one of one sequenced samples and no analysis
    test_case = helpers.add_case(base_store)
    test_sample1 = helpers.add_sample(base_store, sequenced_at=datetime.now())
    test_sample2 = helpers.add_sample(base_store, sequenced_at=None)
    base_store.relate_sample(test_case, test_sample1, "unknown")
    base_store.relate_sample(test_case, test_sample2, "unknown")

    # WHEN getting cases to analyse
    cases = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA, threshold=True)

    # THEN cases should not contain the test case
    assert not cases


def test_one_of_one_sequenced_samples(base_store: Store, helpers):
    """Test that a case with one of one samples that has been sequenced shows up among the
    cases to analyse"""

    # GIVEN a database with a case with one of one sequenced samples and no analysis
    test_case = helpers.add_case(base_store)
    test_sample = helpers.add_sample(base_store, sequenced_at=datetime.now())
    base_store.relate_sample(test_case, test_sample, "unknown")
    assert test_sample.sequenced_at is not None

    # WHEN getting cases to analyse
    cases = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should contain the test case
    assert cases
    assert test_case in cases


def relate_samples(base_store, family, samples):
    """utility function to relate many samples to one case"""

    for sample in samples:
        base_store.relate_sample(family, sample, "unknown")


def add_case_with_samples(base_store, helpers, case_name, n_samples, sequenced_at):
    """utility function to add one case with many samples to use in tests"""

    test_samples = helpers.add_samples(base_store, n_samples)
    for sample in test_samples:
        sample.sequenced_at = sequenced_at
    test_case = helpers.add_case(base_store, case_name)
    relate_samples(base_store, test_case, test_samples)
    return test_case


def add_cases_with_samples(base_store, helpers, n_cases, sequenced_at):
    """utility function to add many cases with two samples to use in tests"""

    cases = []
    for i in range(n_cases):
        case = add_case_with_samples(base_store, helpers, f"f{i}", 2, sequenced_at=sequenced_at)
        cases.append(case)
    return cases
