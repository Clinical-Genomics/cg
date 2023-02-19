"""This script tests the cli methods to add cases to status-db"""
from typing import List, Union

from alchy import Query
from datetime import datetime

from cg.constants import Pipeline
from cg.constants.constants import CaseActions
from cg.constants.subject import Gender, PhenotypeStatus
from cg.store import Store, models
from tests.store_helpers import StoreHelpers


def test_get_families_with_extended_models(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a query is returned from the database"""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: models.Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, pipeline=Pipeline.MIP_DNA
    )

    # Given an action set to analyze
    test_analysis.family.action: str = CaseActions.ANALYZE

    # GIVEN a database with a case with one of one sequenced samples and completed analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting cases to analyse
    cases: List[Query] = list(base_store.get_families_with_analyses())

    case: models.Family = cases[0]

    # THEN cases should be returned
    assert cases

    # THEN analysis should be part of cases attributes
    assert case.analyses[0].pipeline == Pipeline.MIP_DNA


def test_get_families_with_extended_models_when_no_case(base_store: Store):
    """test that no case is returned from the database when no cases"""

    # GIVEN an empty database

    # WHEN getting cases to analyse
    cases: List[Query] = list(base_store.get_families_with_analyses())

    # THEN no cases should be returned
    assert not cases


def test_get_families_with_samples(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a family and samples query is returned from the database."""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: models.Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, pipeline=Pipeline.MIP_DNA
    )

    # GIVEN a database with a case with one of one sequenced samples and completed analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting the stored case with its associated samples
    cases: List[Query] = list(base_store.get_families_with_samples())

    # THEN a list of cases should be returned, and it should contain the stored and linked sample
    assert cases
    assert test_sample == cases[0].links[0].sample


def test_that_many_cases_can_have_one_sample_each(
    base_store: Store, helpers: StoreHelpers, max_nr_of_cases: int, timestamp_now: datetime
):
    """Test that tests that cases are returned even if there are many result rows in the query"""

    # GIVEN a database with max_nr_of_cases cases
    test_cases: List[models.Family] = helpers.add_cases_with_samples(
        base_store, max_nr_of_cases, sequenced_at=timestamp_now
    )

    # WHEN getting cases to analyse
    cases: List[models.Family] = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should contain all cases since they are to be analysed
    assert len(cases) == len(test_cases)


def test_that_cases_can_have_many_samples(
    base_store: Store, helpers, max_nr_of_samples: int, timestamp_now: datetime
):
    """Test that tests that cases are returned even if there are many result rows in the query"""

    # GIVEN a cases with max_nr_of_samples sequenced samples
    case_with_50: models.Family = helpers.add_case_with_samples(
        base_store, "case_with_50_samples", max_nr_of_samples, sequenced_at=timestamp_now
    )

    # GIVEN a sequnced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)
    assert test_sample.sequenced_at

    # GIVEN a case with one sample
    case_with_one: models.Family = helpers.add_case(base_store, "case_with_one_sample")

    # GIVEN a database with a case with one sample sequenced sample
    base_store.relate_sample(case_with_one, test_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting cases to analyse
    cases: List[models.Family] = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should be returned
    assert cases

    # THEN cases should contain the test case
    assert case_with_50 in cases
    assert case_with_one in cases


def test_external_sample_to_re_analyse(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case marked for re-analysis with one sample external not sequenced in-house and
    with completed analysis show up among the cases to analyse."""

    # GIVEN a sample which is not sequenced and external
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=None, is_external=True)

    # GIVEN a completed analysis
    test_analysis: models.Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, pipeline=Pipeline.MIP_DNA
    )
    assert test_analysis.completed_at

    # Given an action set to analyze
    test_analysis.family.action: str = CaseActions.ANALYZE

    # GIVEN a database with a case with one not sequenced external sample
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting cases to analyse
    cases: List[models.Family] = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should be returned
    assert cases

    # THEN test case should be among the cases returned for analysis
    assert test_analysis.family in cases


def test_new_external_case_not_in_result(base_store: Store, helpers: StoreHelpers):
    """Test that a case with one external sample that has no specified data_analysis does not show up"""

    # GIVEN an externally sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=None, is_external=True)

    # GIVEN a cancer case
    test_case: models.Family = helpers.add_case(base_store, data_analysis=Pipeline.BALSAMIC)

    # GIVEN a database with a case with one externally sequenced samples for BALSAMIC analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting cases to analyse
    cases: List[models.Family] = base_store.cases_to_analyze(pipeline=Pipeline.BALSAMIC)

    # THEN cases should not contain the test case
    assert test_case not in cases


def test_case_to_re_analyse(base_store: Store, helpers: StoreHelpers, timestamp_now: datetime):
    """Test that a case marked for re-analyse with one sample that has been sequenced and
    with completed analysis do show up among the cases to analyse"""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: models.Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, pipeline=Pipeline.MIP_DNA
    )

    # Given an action set to analyze
    test_analysis.family.action: str = CaseActions.ANALYZE

    # GIVEN a database with a case with one of one sequenced samples and completed analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting cases to analyse
    cases: List[models.Family] = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should be returned
    assert cases

    # THEN test case should be among the cases returned for analysis
    assert test_analysis.family in cases


def test_all_samples_and_analysis_completed(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case with one sample that has been sequenced and with completed
    analysis don't show up among the cases to analyse"""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: models.Analysis = helpers.add_analysis(base_store, completed_at=timestamp_now)

    # Given a completed analysis
    test_analysis.family.action: Union[None, str] = None

    # GIVEN a database with a case with one of one sequenced samples and completed analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting cases to analyse
    cases: List[models.Family] = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should not contain the test case
    assert not cases


def test_specified_analysis_in_result(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case with one sample that has specified data_analysis does show up"""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case: models.Family = helpers.add_case(base_store, data_analysis=Pipeline.BALSAMIC)

    # GIVEN a database with a case with one sequenced samples for BALSAMIC analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting cases to analyse
    cases: List[models.Family] = base_store.cases_to_analyze(pipeline=Pipeline.BALSAMIC)

    # THEN cases should be returned
    assert cases

    # THEN cases should contain the test case
    assert test_case in cases


def test_exclude_other_pipeline_analysis_from_result(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case with specified analysis and with one sample does not show up among
    others"""

    # GIVEN a sequenced sample
    test_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case = helpers.add_case(base_store, data_analysis=Pipeline.BALSAMIC)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting cases to analyse for another pipeline
    cases: List[models.Family] = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should not contain the test case
    assert test_case not in cases


def test_one_of_two_sequenced_samples(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case with one sequenced samples and one not sequenced sample do not shows up among the
    cases to analyse"""

    # GIVEN a case
    test_case: models.Family = helpers.add_case(base_store)

    # GIVEN a sequenced sample
    sequenced_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a NOT sequenced sample
    not_sequenced_sample: models.Sample = helpers.add_sample(base_store, sequenced_at=None)

    # GIVEN a database with a case with one of one sequenced samples and no analysis
    base_store.relate_sample(test_case, sequenced_sample, PhenotypeStatus.UNKNOWN)
    base_store.relate_sample(test_case, not_sequenced_sample, PhenotypeStatus.UNKNOWN)

    # WHEN getting cases to analyse
    cases: List[models.Family] = base_store.cases_to_analyze(
        pipeline=Pipeline.MIP_DNA, threshold=True
    )

    # THEN no cases should be returned
    assert not cases


def test_one_of_one_sequenced_samples(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case with one of one samples that has been sequenced shows up among the
    cases to analyse"""

    # GIVEN a case
    test_case: models.Family = helpers.add_case(base_store)

    # GIVEN a sequenced sample
    test_sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a database with a case with a sequenced samples and no analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)
    assert test_sample.sequenced_at is not None

    # WHEN getting cases to analyse
    cases: List[models.Family] = base_store.cases_to_analyze(pipeline=Pipeline.MIP_DNA)

    # THEN cases should be returned
    assert cases

    # THEN cases should contain the test case
    assert test_case in cases
