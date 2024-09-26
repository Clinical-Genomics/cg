"""Tests the findbusinessdata part of the Cg store API related to Analysis model."""

from datetime import datetime

from sqlalchemy.orm import Query

from cg.constants import Workflow
from cg.constants.constants import CaseActions
from cg.constants.subject import PhenotypeStatus
from cg.store.models import Analysis, Case, CaseSample, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_get_latest_nipt_analysis_to_upload(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store,
    timestamp_now: datetime,
    workflow: str = Workflow.FLUFFY,
):
    """Test get the latest NIPT analysis to upload."""
    # GIVEN an analysis that is not delivery reported but there exists a newer analysis

    # WHEN fetching the latest analysis to upload to nipt
    analyses: list[Analysis] = (
        store_with_analyses_for_cases_not_uploaded_fluffy.get_latest_analysis_to_upload_for_workflow(
            workflow=workflow
        )
    )

    # THEN only the newest analysis should be returned
    for analysis in analyses:
        assert analysis.started_at == timestamp_now
        assert analysis.uploaded_at is None
        assert analysis.workflow == workflow


def test_get_latest_microsalt_analysis_to_upload(
    store_with_analyses_for_cases_not_uploaded_microsalt: Store,
    timestamp_now: datetime,
    workflow: str = Workflow.MICROSALT,
):
    """Test get the latest microsalt analysis to upload."""
    # GIVEN an analysis that is not delivery reported but there exists a newer analysis

    # WHEN fetching the latest analysis to upload to microsalt
    analyses: list[Analysis] = (
        store_with_analyses_for_cases_not_uploaded_microsalt.get_latest_analysis_to_upload_for_workflow(
            workflow=workflow
        )
    )

    # THEN only the newest analysis should be returned
    for analysis in analyses:
        assert analysis.started_at == timestamp_now
        assert analysis.uploaded_at is None
        assert analysis.workflow == workflow


def test_get_analyses_to_deliver_for_pipeline(
    store_with_analyses_for_cases_to_deliver: Store,
    workflow: Workflow = Workflow.FLUFFY,
):
    # GIVEN a store with multiple analyses to deliver

    # WHEN fetching the latest analysis to upload to nipt
    analyses = store_with_analyses_for_cases_to_deliver.get_analyses_to_deliver_for_pipeline(
        workflow=workflow
    )

    # THEN only the newest analysis should be returned
    for analysis in analyses:
        assert analysis.case.internal_id in ["test_case_1", "yellowhog"]
        assert analysis.uploaded_at is None
        assert analysis.workflow == workflow


def test_get_analyses(store_with_analyses_for_cases: Store):
    """Test all analyses can be returned."""
    # GIVEN a database with an analysis and case

    # WHEN fetching all analyses
    analysis: list[Analysis] = store_with_analyses_for_cases.get_analyses()

    # THEN one analysis should be returned
    assert len(analysis) == store_with_analyses_for_cases._get_query(table=Analysis).count()


def test_get_families_with_extended_models(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a query is returned from the database."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, workflow=Workflow.MIP_DNA
    )

    # Given an action set to analyze
    test_analysis.case.action: str = CaseActions.ANALYZE

    # GIVEN a database with a case with one of sequenced samples and completed analysis
    link = base_store.relate_sample(test_analysis.case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)

    # WHEN getting cases to analyse
    cases: list[Query] = list(base_store._get_outer_join_cases_with_analyses_query())

    case: Case = cases[0]

    # THEN cases should be returned
    assert cases

    # THEN analysis should be part of cases attributes
    assert case.analyses[0].workflow == Workflow.MIP_DNA


def test_get_families_with_extended_models_when_no_case(base_store: Store):
    """test that no case is returned from the database when no cases."""

    # GIVEN an empty database

    # WHEN getting cases to analyse
    cases: list[Query] = list(base_store._get_outer_join_cases_with_analyses_query())

    # THEN no cases should be returned
    assert not cases


def test_get_cases_with_samples_query(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case and samples query is returned from the database."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, workflow=Workflow.MIP_DNA
    )

    # GIVEN a database with a case with one of sequenced samples and completed analysis
    link = base_store.relate_sample(test_analysis.case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)

    # WHEN getting the stored case with its associated samples
    cases: list[Query] = list(base_store._get_join_cases_with_samples_query())

    # THEN a list of cases should be returned, and it should contain the stored and linked sample
    assert cases
    assert test_sample == cases[0].links[0].sample


def test_that_many_cases_can_have_one_sample_each(
    base_store: Store, helpers: StoreHelpers, max_nr_of_cases: int, timestamp_now: datetime
):
    """Test that tests that cases are returned even if there are many result rows in the query."""

    # GIVEN a database with max_nr_of_cases cases
    test_cases: list[Case] = helpers.add_cases_with_samples(
        base_store, max_nr_of_cases, sequenced_at=timestamp_now
    )

    # WHEN getting cases to analyse
    cases: list[Case] = base_store.cases_to_analyse(workflow=Workflow.MIP_DNA)

    # THEN cases should contain all cases since they are to be analysed
    assert len(cases) == len(test_cases)


def test_that_cases_can_have_many_samples(
    base_store: Store, helpers, max_nr_of_samples: int, timestamp_now: datetime
):
    """Test that tests that cases are returned even if there are many result rows in the query."""

    # GIVEN a cases with max_nr_of_samples sequenced samples
    case_with_50: Case = helpers.add_case_with_samples(
        base_store, "case_with_50_samples", max_nr_of_samples, sequenced_at=timestamp_now
    )

    # GIVEN a sequnced sample
    test_sample: Sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)
    assert test_sample.last_sequenced_at

    # GIVEN a case with one sample
    case_with_one: Case = helpers.add_case(base_store, "case_with_one_sample")

    # GIVEN a database with a case with one sample sequenced sample
    link = base_store.relate_sample(case_with_one, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)

    # WHEN getting cases to analyse
    cases: list[Case] = base_store.cases_to_analyse(workflow=Workflow.MIP_DNA)

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
    test_sample: Sample = helpers.add_sample(base_store, is_external=True, last_sequenced_at=None)

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, workflow=Workflow.MIP_DNA
    )
    assert test_analysis.completed_at

    # Given an action set to analyze
    test_analysis.case.action: str = CaseActions.ANALYZE

    # GIVEN a database with a case with one not sequenced external sample
    link = base_store.relate_sample(test_analysis.case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)

    # WHEN getting cases to analyse
    cases: list[Case] = base_store.cases_to_analyse(workflow=Workflow.MIP_DNA)

    # THEN cases should be returned
    assert cases

    # THEN test case should be among the cases returned for analysis
    assert test_analysis.case in cases


def test_new_external_case_not_in_result(base_store: Store, helpers: StoreHelpers):
    """Test that a case with one external sample that has no specified data_analysis does not show up."""

    # GIVEN an externally sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, is_external=True, last_sequenced_at=None)

    # GIVEN a cancer case
    test_case: Case = helpers.add_case(base_store, data_analysis=Workflow.BALSAMIC)

    # GIVEN a database with a case with one externally sequenced samples for BALSAMIC analysis
    link = base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)

    # WHEN getting cases to analyse
    cases: list[Case] = base_store.cases_to_analyse(workflow=Workflow.BALSAMIC)

    # THEN cases should not contain the test case
    assert test_case not in cases


def test_case_to_re_analyse(base_store: Store, helpers: StoreHelpers, timestamp_now: datetime):
    """Test that a case marked for re-analyse with one sample that has been sequenced and
    with completed analysis do show up among the cases to analyse."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, workflow=Workflow.MIP_DNA
    )

    # Given an action set to analyze
    test_analysis.case.action: str = CaseActions.ANALYZE

    # GIVEN a database with a case with one of one sequenced samples and completed analysis
    link = base_store.relate_sample(test_analysis.case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)

    # WHEN getting cases to analyse
    cases: list[Case] = base_store.cases_to_analyse(workflow=Workflow.MIP_DNA)

    # THEN cases should be returned
    assert cases

    # THEN test case should be among the cases returned for analysis
    assert test_analysis.case in cases


def test_all_samples_and_analysis_completed(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case with one sample that has been sequenced and with completed
    analysis don't show up among the cases to analyse."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(base_store, completed_at=timestamp_now)

    # Given a completed analysis
    test_analysis.case.action: str | None = None

    # GIVEN a database with a case with one of one sequenced samples and completed analysis
    link = base_store.relate_sample(test_analysis.case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)

    # WHEN getting cases to analyse
    cases: list[Case] = base_store.cases_to_analyse(workflow=Workflow.MIP_DNA)

    # THEN cases should not contain the test case
    assert not cases


def test_specified_analysis_in_result(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case with one sample that has specified data_analysis does show up."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case: Case = helpers.add_case(base_store, data_analysis=Workflow.BALSAMIC)

    # GIVEN a database with a case with one sequenced samples for BALSAMIC analysis
    link = base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)

    # WHEN getting cases to analyse
    cases: list[Case] = base_store.cases_to_analyse(workflow=Workflow.BALSAMIC)

    # THEN cases should be returned
    assert cases

    # THEN cases should contain the test case
    assert test_case in cases


def test_exclude_other_pipeline_analysis_from_result(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case with specified analysis and with one sample does not show up among
    others."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case = helpers.add_case(base_store, data_analysis=Workflow.BALSAMIC)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    link = base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)

    # WHEN getting cases to analyse for another workflow
    cases: list[Case] = base_store.cases_to_analyse(workflow=Workflow.MIP_DNA)

    # THEN cases should not contain the test case
    assert test_case not in cases


def test_one_of_one_sequenced_samples(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case with one of one samples that has been sequenced shows up among the
    cases to analyse."""

    # GIVEN a case
    test_case: Case = helpers.add_case(base_store)

    # GIVEN a sequenced sample
    test_sample = helpers.add_sample(base_store, last_sequenced_at=timestamp_now)

    # GIVEN a database with a case with a sequenced samples and no analysis
    link = base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.session.add(link)
    assert test_sample.last_sequenced_at is not None

    # WHEN getting cases to analyse
    cases: list[Case] = base_store.cases_to_analyse(workflow=Workflow.MIP_DNA)

    # THEN cases should be returned
    assert cases

    # THEN cases should contain the test case
    assert test_case in cases


def test_get_analyses_for_case_and_pipeline_before(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store,
    timestamp_now: datetime,
    workflow: Workflow = Workflow.FLUFFY,
    case_id: str = "yellowhog",
):
    """Test to get all analyses before a given date."""

    # GIVEN a database with a number of analyses

    # WHEN getting all analyses before a given date
    analyses: list[Analysis] = (
        store_with_analyses_for_cases_not_uploaded_fluffy.get_analyses_for_case_and_workflow_started_at_before(
            workflow=workflow, started_at_before=timestamp_now, case_internal_id=case_id
        )
    )

    # THEN assert that the analyses before the given date are returned
    for analysis in analyses:
        assert analysis.started_at < timestamp_now
        assert analysis.case.internal_id == case_id
        assert analysis.workflow == workflow


def test_get_analyses_for_case_before(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store,
    timestamp_now: datetime,
    case_id: str = "yellowhog",
):
    """Test to get all analyses before a given date."""

    # GIVEN a database with a number of analyses

    # WHEN getting all analyses before a given date
    analyses: list[Analysis] = (
        store_with_analyses_for_cases_not_uploaded_fluffy.get_analyses_for_case_started_at_before(
            case_internal_id=case_id,
            started_at_before=timestamp_now,
        )
    )

    # THEN assert that the analyses before the given date are returned
    for analysis in analyses:
        assert analysis.started_at < timestamp_now
        assert analysis.case.internal_id == case_id


def test_get_analyses_for_pipeline_before(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store,
    timestamp_now: datetime,
    workflow: Workflow = Workflow.FLUFFY,
):
    """Test to get all analyses for a workflow before a given date."""

    # GIVEN a database with a number of analyses

    # WHEN getting all analyses before a given date
    analyses: list[Analysis] = (
        store_with_analyses_for_cases_not_uploaded_fluffy.get_analyses_for_workflow_started_at_before(
            workflow=workflow, started_at_before=timestamp_now
        )
    )

    # THEN assert that the analyses before the given date are returned
    for analysis in analyses:
        assert analysis.started_at < timestamp_now
        assert analysis.workflow == workflow


def test_get_analyses_before(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store,
    timestamp_now: datetime,
):
    """Test to get all analyses for a workflow before a given date."""

    # GIVEN a database with a number of analyses

    # WHEN getting all analyses before a given date
    analyses: list[Analysis] = (
        store_with_analyses_for_cases_not_uploaded_fluffy.get_analyses_started_at_before(
            started_at_before=timestamp_now
        )
    )

    # THEN assert that the analyses before the given date are returned
    for analysis in analyses:
        assert analysis.started_at < timestamp_now


def test_get_analysis_by_entry_id(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store,
):
    """Test to get an analysis by entry id."""

    # GIVEN a database with a number of analyses

    # WHEN getting an analysis by entry id
    analysis: Analysis = store_with_analyses_for_cases_not_uploaded_fluffy.get_analysis_by_entry_id(
        entry_id=1
    )

    # THEN assert that the analysis is returned
    assert analysis.id == 1
