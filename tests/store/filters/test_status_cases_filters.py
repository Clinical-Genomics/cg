from datetime import datetime, timedelta

from sqlalchemy.orm import Query

from cg.constants.constants import CaseActions, DataDelivery, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.constants.subject import PhenotypeStatus
from cg.store.filters.status_case_filters import (
    filter_case_by_internal_id,
    filter_cases_by_case_search,
    filter_cases_by_customer_entry_ids,
    filter_cases_by_entry_id,
    filter_cases_by_name,
    filter_cases_by_priority,
    filter_cases_by_workflow_search,
    filter_cases_for_analysis,
    filter_cases_has_sequence,
    filter_cases_not_analysed,
    filter_cases_with_loqusdb_supported_sequencing_method,
    filter_cases_with_loqusdb_supported_workflow,
    filter_cases_with_scout_data_delivery,
    filter_cases_with_workflow,
    filter_inactive_analysis_cases,
    filter_newer_cases_by_order_date,
    filter_older_cases_by_creation_date,
    filter_report_supported_data_delivery_cases,
    filter_running_cases,
)
from cg.store.models import Analysis, Case, CaseSample, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_filter_cases_has_sequence(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when there is a case with a sequenced sample."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(store=base_store, last_sequenced_at=timestamp_now)

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse
    cases: Query = filter_cases_has_sequence(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases


def test_filter_cases_has_sequence_when_external(base_store: Store, helpers: StoreHelpers):
    """Test that a case is returned when there is a case with an externally sequenced sample."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(
        store=base_store, is_external=True, last_sequenced_at=None
    )

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse
    cases: Query = filter_cases_has_sequence(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases


def test_filter_cases_has_sequence_when_not_sequenced(base_store: Store, helpers: StoreHelpers):
    """Test that no case is returned when there is a case with a sample that has not been sequenced."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(store=base_store, last_sequenced_at=None)

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_has_sequence(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should not contain the test case
    assert not cases.all()


def test_filter_cases_has_sequence_when_not_external_nor_sequenced(
    base_store: Store, helpers: StoreHelpers
):
    """Test that no case is returned when there is a case with a sample that has not been sequenced nor is external."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(
        store=base_store, is_external=False, last_sequenced_at=None
    )

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_has_sequence(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should not contain the test case
    assert not cases.all()


def test_filter_cases_with_workflow_when_correct_workflow(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that no case is returned when there are no cases with the specified workflow."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(store=base_store, last_sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case = helpers.add_case(store=base_store, data_analysis=Workflow.BALSAMIC)

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse for another workflow
    cases: list[Query] = list(filter_cases_with_workflow(cases=cases, workflow=Workflow.BALSAMIC))

    # THEN cases should contain the test case
    assert cases


def test_filter_cases_with_workflow_when_incorrect_workflow(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that no case is returned when there are no cases with the specified workflow."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(store=base_store, last_sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case: Case = helpers.add_case(store=base_store, data_analysis=Workflow.BALSAMIC)

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse for another workflow
    cases: list[Query] = list(filter_cases_with_workflow(cases=cases, workflow=Workflow.MIP_DNA))

    # THEN cases should not contain the test case
    assert not cases


def test_filter_cases_with_loqusdb_supported_workflow(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test retrieval of cases that support Loqusdb upload."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(store=base_store, last_sequenced_at=timestamp_now)

    # GIVEN a MIP-DNA and a FLUFFY case
    test_mip_case: Case = helpers.add_case(store=base_store, data_analysis=Workflow.MIP_DNA)
    test_mip_case.customer.loqus_upload = True
    test_fluffy_case: Case = helpers.add_case(
        store=base_store, name="test", data_analysis=Workflow.FLUFFY
    )
    test_fluffy_case.customer.loqus_upload = True

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link_1: CaseSample = base_store.relate_sample(
        case=test_mip_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    link_2: CaseSample = base_store.relate_sample(
        case=test_fluffy_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add_all([link_1, link_2])

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases with workflow
    cases: list[Query] = list(filter_cases_with_loqusdb_supported_workflow(cases=cases))

    # THEN only the Loqusdb supported case should be extracted
    assert test_mip_case in cases
    assert test_fluffy_case not in cases


def test_filter_cases_with_loqusdb_supported_sequencing_method(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test retrieval of cases with a valid Loqusdb sequencing method."""

    # GIVEN a sample with a valid Loqusdb sequencing method
    test_sample_wes: Sample = helpers.add_sample(
        store=base_store,
        application_type=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        last_sequenced_at=timestamp_now,
    )

    # GIVEN a MIP-DNA associated test case
    test_case_wes: Case = helpers.add_case(store=base_store, data_analysis=Workflow.MIP_DNA)
    link = base_store.relate_sample(
        case=test_case_wes, sample=test_sample_wes, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN retrieving the available cases
    cases: Query = filter_cases_with_loqusdb_supported_sequencing_method(
        cases=cases, workflow=Workflow.MIP_DNA
    )

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN the expected case should be retrieved
    assert test_case_wes in cases


def test_filter_cases_with_loqusdb_supported_sequencing_method_empty(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test return of cases with a valid Loqusdb sequencing method."""

    # GIVEN a not supported loqusdb sample
    test_sample_wts: Sample = helpers.add_sample(
        store=base_store, is_rna=True, name="sample_wts", last_sequenced_at=timestamp_now
    )

    # GIVEN a MIP-DNA associated test case
    test_case_wts: Case = helpers.add_case(store=base_store, data_analysis=Workflow.MIP_DNA)
    link = base_store.relate_sample(
        case=test_case_wts, sample=test_sample_wts, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN retrieving the valid cases
    cases: Query = filter_cases_with_loqusdb_supported_sequencing_method(
        cases=cases, workflow=Workflow.MIP_DNA
    )

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN no cases should be returned
    assert not cases.all()


def test_filter_cases_for_analysis(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when there is a case with an action set to analyze."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(store=base_store, last_sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(
        store=base_store, completed_at=timestamp_now, workflow=Workflow.MIP_DNA
    )

    # Given an action set to analyze
    test_analysis.case.action = CaseActions.ANALYZE

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_analysis.case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert test_analysis.case in cases


def test_filter_cases_for_analysis_that_is_running_multiple_analyses_and_one_analysis_is_older_than_last_sequenced(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime, timestamp_yesterday: datetime
):
    """Test that a case is not returned if case action is running and when there are miltiple analyses where one analysis is older than a sample is last sequenced."""

    # GIVEN a case
    test_case: Case = helpers.add_case(base_store)

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(store=base_store, last_sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(
        store=base_store, case=test_case, workflow=Workflow.MIP_DNA
    )

    # GIVEN a completed analysis older than the sample last sequenced
    test_analysis_2: Analysis = helpers.add_analysis(
        store=base_store,
        case=test_case,
        started_at=timestamp_yesterday,
        completed_at=timestamp_yesterday,
        workflow=Workflow.MIP_DNA,
    )
    # GIVEN an old analysis
    test_analysis_2.created_at = timestamp_yesterday

    # Given an action set to running
    test_analysis.case.action = CaseActions.RUNNING

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_analysis.case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should not contain the test case
    assert test_analysis.case not in cases


def test_filter_cases_for_analysis_multiple_analyses_and_one_analysis_is_older_than_last_sequenced(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime, timestamp_yesterday: datetime
):
    """Test that a case is returned if case action is None and when there are miltiple analyses where one analysis is older than a sample is last sequenced."""

    # GIVEN a case
    test_case: Case = helpers.add_case(base_store, data_analysis=Workflow.MICROSALT)

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(store=base_store, last_sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(
        store=base_store, case=test_case, completed_at=timestamp_now, workflow=Workflow.MICROSALT
    )

    # GIVEN a completed analysis older than the sample last sequenced
    test_analysis_2: Analysis = helpers.add_analysis(
        store=base_store,
        case=test_case,
        started_at=timestamp_yesterday,
        completed_at=timestamp_yesterday,
        workflow=Workflow.MICROSALT,
    )
    # GIVEN an old analysis
    test_analysis_2.created_at = timestamp_yesterday

    # Given an action set to None
    test_analysis.case.action = None

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_analysis.case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert test_analysis.case in cases


def test_filter_cases_for_analysis_multiple_analyses_and_one_analysis_is_not_older_than_last_sequenced_and_one_is(
    base_store: Store,
    helpers: StoreHelpers,
    timestamp_now: datetime,
    timestamp_yesterday: datetime,
    old_timestamp: datetime,
):
    """Test that a case is returned if case action is None and when there are miltiple analyses where one analysis is older than a sample is last sequenced."""

    # GIVEN a case
    test_case: Case = helpers.add_case(base_store, data_analysis=Workflow.MICROSALT)

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(
        store=base_store, last_sequenced_at=timestamp_yesterday
    )

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(
        store=base_store,
        case=test_case,
        started_at=timestamp_yesterday,
        completed_at=timestamp_now,
        workflow=Workflow.MICROSALT,
    )

    # GIVEN a completed analysis older than the sample last sequenced
    test_analysis_2: Analysis = helpers.add_analysis(
        store=base_store,
        case=test_case,
        started_at=timestamp_yesterday,
        completed_at=timestamp_yesterday,
        workflow=Workflow.MICROSALT,
    )
    # GIVEN an old analysis
    test_analysis_2.created_at = old_timestamp

    # Given an action set to None
    test_analysis.case.action = None

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_analysis.case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert test_analysis.case in cases


def test_filter_cases_for_analysis_when_sequenced_sample_and_no_analysis(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when there are internally created cases with no action set and no prior analysis."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(
        store=base_store, is_external=False, last_sequenced_at=timestamp_now
    )

    # GIVEN a case
    test_case: Case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert test_case in cases


def test_filter_cases_for_analysis_when_cases_with_no_action_and_new_sequence_data(
    base_store: Store,
    helpers: StoreHelpers,
    timestamp_yesterday: datetime,
    timestamp_now: datetime,
):
    """Test that a case is returned when cases with no action, but new sequence data."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(
        store=base_store, is_external=False, last_sequenced_at=timestamp_now
    )

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(store=base_store, workflow=Workflow.MICROSALT)

    # Given an action set to None
    test_analysis.case.action = None

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_analysis.case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN an old analysis
    test_analysis.created_at = timestamp_yesterday

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert test_analysis.case in cases


def test_filter_cases_for_analysis_when_cases_with_no_action_and_old_sequence_data(
    base_store: Store, helpers: StoreHelpers, timestamp_yesterday: datetime
):
    """Test that a case is not returned when cases with no action, but old sequence data."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(
        store=base_store, is_external=True, last_sequenced_at=timestamp_yesterday
    )

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(store=base_store, workflow=Workflow.MIP_DNA)

    # Given an action set to None
    test_analysis.case.action = None

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_analysis.case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN no cases should be returned
    assert not cases.all()


def test_filter_cases_for_analysis_top_up(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime, timestamp_yesterday: datetime
):
    """
    Test that a case is returned when there is a case with an action set to top-up and has new
    sequencing data.
    """
    # GIVEN a sampled sequenced just now
    test_sample: Sample = helpers.add_sample(
        store=base_store, is_external=False, last_sequenced_at=timestamp_now
    )

    # GIVEN a case with action set to "top-up"
    test_case: Case = helpers.add_case(
        store=base_store, name="test_case", action=CaseActions.TOP_UP
    )

    # GIVEN that the sample and the case are related
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.AFFECTED
    )

    # GIVEN an analysis for the case completed yesterday
    test_analysis: Analysis = helpers.add_analysis(
        store=base_store,
        workflow=Workflow.MIP_DNA,
        case=test_case,
    )
    test_analysis.created_at = timestamp_yesterday
    base_store.session.add(link)
    base_store.session.add(test_analysis)

    # GIVEN a cases Query
    cases: Query = base_store._get_case_query_for_analysis_start()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # THEN assert that cases is a query
    assert isinstance(cases, Query)

    # THEN assert that query is not empty
    assert isinstance(cases.first(), Case)

    # THEN cases should contain the test case
    assert cases.first() == test_case


def test_filter_cases_for_analysis_top_up_multiple_analyses(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime, timestamp_yesterday: datetime
):
    """
    Test that only the latest analysis is considered for the top-up case.
    """
    # GIVEN a sampled sequenced twelve hours ago
    test_sample: Sample = helpers.add_sample(
        store=base_store,
        is_external=False,
        last_sequenced_at=timestamp_now - timedelta(hours=12),
    )

    # GIVEN a case with action set to "top-up"
    test_case: Case = helpers.add_case(
        store=base_store, name="test_case", action=CaseActions.TOP_UP
    )

    # GIVEN that the sample and the case are related
    helpers.relate_samples(base_store=base_store, case=test_case, samples=[test_sample])

    # GIVEN an analysis for the case completed yesterday
    test_analysis: Analysis = helpers.add_analysis(
        store=base_store,
        created_at=timestamp_yesterday,
        workflow=Workflow.MIP_DNA,
        case=test_case,
    )
    test_analysis.created_at = timestamp_yesterday

    # GIVEN an analysis for the case completed now
    helpers.add_analysis(
        store=base_store,
        created_at=timestamp_now,
        workflow=Workflow.MIP_DNA,
        case=test_case,
    )

    # GIVEN a cases Query
    cases: Query = base_store._get_case_query_for_analysis_start()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # THEN assert that query is empty
    assert len(cases.all()) == 0


def test_filter_cases_for_analysis_top_up_when_no_new_sequence_data(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime, timestamp_yesterday: datetime
):
    """
    Test that a case is not returned when there is a case with an action set to top-up and has no new
    sequencing data.
    """
    # GIVEN a sampled sequenced yesterday
    test_sample: Sample = helpers.add_sample(
        store=base_store, is_external=False, last_sequenced_at=timestamp_yesterday
    )

    # GIVEN a case with action set to "top-up"
    test_case: Case = helpers.add_case(
        store=base_store, name="test_case", action=CaseActions.TOP_UP
    )

    # GIVEN that the sample and the case are related
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.AFFECTED
    )

    # GIVEN an analysis for the case completed now
    test_analysis: Analysis = helpers.add_analysis(
        store=base_store,
        workflow=Workflow.MIP_DNA,
        case=test_case,
    )
    test_analysis.created_at = timestamp_now

    base_store.session.add(link)
    base_store.session.add(test_analysis)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyze
    cases: Query = filter_cases_for_analysis(cases=cases)

    # THEN assert that cases is a query
    assert isinstance(cases, Query)

    # THEN assert that query is empty
    assert not cases.all()


def test_filter_cases_with_scout_data_delivery(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when Scout is specified as a data delivery option."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store)

    # GIVEN a case with Scout as data delivery
    test_case = helpers.add_case(store=base_store, data_delivery=DataDelivery.FASTQ_ANALYSIS_SCOUT)

    # GIVEN a database with a case with one sequenced sample for specified analysis
    link = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add(link)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases with Scout as the data delivery option
    cases: Query = filter_cases_with_scout_data_delivery(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert test_case in cases


def test_filter_report_supported_data_delivery_cases(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned for a delivery report supported data delivery option."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store)

    # GIVEN a case with Scout and a not supported option as data deliveries
    test_case = helpers.add_case(store=base_store, data_delivery=DataDelivery.FASTQ_ANALYSIS_SCOUT)
    test_invalid_case = helpers.add_case(
        store=base_store, name="test", data_delivery=DataDelivery.FASTQ
    )

    # GIVEN a database with the test cases
    link_1: CaseSample = base_store.relate_sample(
        case=test_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    link_2: CaseSample = base_store.relate_sample(
        case=test_invalid_case, sample=test_sample, status=PhenotypeStatus.UNKNOWN
    )
    base_store.session.add_all([link_1, link_2])

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN retrieving the delivery report supported cases
    cases: Query = filter_report_supported_data_delivery_cases(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN only the delivery report supported case should be retrieved
    assert test_case in cases
    assert test_invalid_case not in cases


def test_filter_inactive_analysis_cases(base_store: Store, helpers: StoreHelpers):
    """Test that an inactive case is returned when there is a case that has no action set."""

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a cases Query
    cases: Query = base_store._get_query(table=Case)

    # WHEN getting completed cases
    cases: Query = filter_inactive_analysis_cases(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases

    assert cases.all()[0].internal_id == test_case.internal_id


def test_filter_inactive_analysis_cases_when_on_hold(base_store: Store, helpers: StoreHelpers):
    """Test that an inactivated case is returned when there is a case that has action set to hold."""

    # GIVEN a case
    test_case = helpers.add_case(store=base_store, action=CaseActions.HOLD)

    # GIVEN a cases Query
    cases: Query = base_store._get_query(table=Case)

    # WHEN getting completed cases
    cases: Query = filter_inactive_analysis_cases(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases

    assert cases[0].internal_id == test_case.internal_id


def test_filter_inactive_analysis_cases_when_not_completed(
    base_store: Store, helpers: StoreHelpers
):
    """Test that no case is returned when there is a case that, has an action set to running."""

    # GIVEN a case
    helpers.add_case(store=base_store, action=CaseActions.RUNNING)

    # GIVEN a cases Query
    cases: Query = base_store._get_query(table=Case)

    # WHEN getting completed cases
    cases: Query = filter_inactive_analysis_cases(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should not contain the test case
    assert not cases.all()


def test_get_old_cases(base_store: Store, helpers: StoreHelpers, timestamp_in_2_weeks: datetime):
    """Test that an old case is returned when a future date is supplied."""

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a cases Query
    cases: Query = base_store._get_query(table=Case)

    # WHEN getting completed cases
    cases: Query = filter_older_cases_by_creation_date(
        cases=cases, creation_date=timestamp_in_2_weeks
    )

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases

    assert cases.all()[0].internal_id == test_case.internal_id


def test_get_old_cases_none_when_all_cases_are_too_new(
    base_store: Store, helpers: StoreHelpers, timestamp_yesterday: datetime
):
    """No cases are returned when all cases in the store are too new."""

    # GIVEN a case
    helpers.add_case(base_store)

    # GIVEN a cases Query
    cases: Query = base_store._get_query(table=Case)

    # WHEN getting completed cases
    cases: Query = filter_older_cases_by_creation_date(
        cases=cases, creation_date=timestamp_yesterday
    )

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should not contain the test case
    assert not cases.all()


def test_filter_case_by_existing_entry_id(store_with_multiple_cases_and_samples: Store):
    # GIVEN a store containing a case with an entry id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    entry_id: int = cases_query.first().id
    assert entry_id

    # WHEN filtering for cases with the entry_id
    cases: Query = filter_cases_by_entry_id(cases=cases_query, entry_id=entry_id)

    # THEN the case should have the entry_id
    assert cases.first().id == entry_id


def test_filter_cases_by_non_existing_entry_id(
    store_with_multiple_cases_and_samples: Store, non_existent_id: str
):
    # GIVEN a store containing cases without a specific entry id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    entry_ids = [case.id for case in cases_query.all()]
    assert non_existent_id not in entry_ids

    # WHEN filtering for cases with the non-existing entry id
    cases: Query = filter_cases_by_entry_id(cases=cases_query, entry_id=non_existent_id)

    # THEN the query should contain no cases
    assert cases.count() == 0


def test_filter_case_by_existing_internal_id(
    store_with_multiple_cases_and_samples: Store, case_id: str
):
    # GIVEN a store containing a case with an internal id case_id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    internal_ids = [case.internal_id for case in cases_query.all()]
    assert case_id in internal_ids

    # WHEN filtering for cases with the internal id case_id
    cases: Query = filter_case_by_internal_id(cases=cases_query, internal_id=case_id)

    # THEN the query should contain only one case
    assert cases.count() == 1

    # THEN the case should have the case id as the internal id
    assert cases.first().internal_id == case_id


def test_filter_cases_by_non_existing_internal_id(
    store_with_multiple_cases_and_samples: Store, non_existent_id: str
):
    # GIVEN a store containing a case with an internal id case_id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    internal_ids = [case.internal_id for case in cases_query.all()]
    assert non_existent_id not in internal_ids

    # WHEN filtering for cases with the internal id case_id
    cases: Query = filter_case_by_internal_id(cases=cases_query, internal_id=non_existent_id)

    # THEN the query should contain no cases
    assert cases.count() == 0


def test_filter_case_by_empty_internal_id(store_with_multiple_cases_and_samples: Store):
    # GIVEN a store containing cases
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)

    # WHEN filtering for cases with an empty internal id
    cases: Query = filter_case_by_internal_id(cases=cases_query, internal_id="")

    # THEN the query should return no cases
    assert cases.count() == 0


def test_filter_running_cases_no_running_cases(store_with_multiple_cases_and_samples: Store):
    """Test that no cases are returned when no cases have a running action."""
    # GIVEN a store containing cases with no "running" action
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    cases_query = cases_query.filter(Case.action != CaseActions.RUNNING)

    # WHEN getting active cases
    active_cases: Query = filter_running_cases(cases=cases_query)

    # THEN the query should return no cases
    assert active_cases.count() == 0


def test_filter_running_cases_with_running_cases(store_with_multiple_cases_and_samples: Store):
    """Test that at least one case is returned when at least one case has a running action."""
    # GIVEN a store containing cases with at least one "running" action
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    actions: list[str] = [case.action for case in cases_query.all()]
    assert CaseActions.RUNNING in actions

    # WHEN getting active cases
    active_cases: Query = filter_running_cases(cases=cases_query)

    # THEN the query should return at least one case
    assert active_cases.count() >= 1


def test_filter_running_cases_only_running_cases(store_with_multiple_cases_and_samples: Store):
    """Test that all cases are returned when all cases have a running action."""
    # GIVEN a store containing only cases with "running" action
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    for case in cases_query.all():
        case.action = CaseActions.RUNNING

    # WHEN getting active cases
    active_cases: Query = filter_running_cases(cases=cases_query)

    # THEN the query should return the same number of cases as the original query
    assert active_cases.count() == cases_query.count()


def test_filter_cases_by_customer_entry_ids(store_with_multiple_cases_and_samples: Store):
    """Test that cases are returned when filtering by customer entry ids."""
    # GIVEN a store containing cases with customer ids
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    customer_ids = [case.customer_id for case in cases_query.all()]
    assert customer_ids

    # WHEN filtering cases by customer ids
    filtered_cases: Query = filter_cases_by_customer_entry_ids(
        cases=cases_query, customer_entry_ids=customer_ids
    )

    # THEN the filtered_cases should have the same count as cases_query
    assert filtered_cases.count() == cases_query.count()

    # THEN all cases in filtered_cases should have a customer id in the customer ids list
    for case in filtered_cases:
        assert case.customer_id in customer_ids


def test_filter_cases_by_name(store_with_multiple_cases_and_samples: Store):
    """Test that cases are returned when filtering by name."""
    # GIVEN a store containing cases with various names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    test_name = cases_query.first().name

    # WHEN filtering cases by a specific name
    filtered_cases: Query = filter_cases_by_name(cases=cases_query, name=test_name)

    # THEN all cases in filtered_cases should have the specified name
    for case in filtered_cases:
        assert case.name == test_name


def test_filter_cases_by_search_pattern(store_with_multiple_cases_and_samples: Store):
    """Test that cases are returned when filtering by matching internal ids."""
    # GIVEN a store containing cases with internal ids and names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    test_internal_id_pattern = cases_query.first().internal_id[:3]
    test_name_pattern = cases_query.first().name[:3]

    # WHEN filtering cases by matching internal id or name
    filtered_cases: Query = filter_cases_by_case_search(
        cases=cases_query,
        case_search=test_internal_id_pattern,
        name_search_pattern=test_name_pattern,
    )

    # THEN at least one case in filtered_cases should have an internal_id or name matching the specified patterns
    assert any(
        case.internal_id.startswith(test_internal_id_pattern)
        or case.name.startswith(test_name_pattern)
        for case in filtered_cases
    )


def test_filter_cases_not_analysed_no_cases(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases are returned when all cases have been analyzed."""
    # GIVEN a store containing only cases that have been analyzed
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    for case in cases_query.all():
        case.analyses.append(Analysis(completed_at=datetime.now()))

    # WHEN filtering cases for cases that have not been analyzed
    filtered_cases: Query = filter_cases_not_analysed(cases=cases_query)

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_cases_not_analysed_no_cases_in_progress(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that all cases are returned when no cases are in progress."""
    # GIVEN a store containing cases that have not been analyzed and no cases are in progress
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    for case in cases_query.all():
        case.analyses = []
        case.action = CaseActions.HOLD

    # WHEN filtering cases for cases that have not been analyzed
    filtered_cases: Query = filter_cases_not_analysed(cases=cases_query)

    # THEN the query should return all cases
    assert filtered_cases.count() == cases_query.count()


def test_filter_cases_not_analysed_in_progress(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases in progress are returned."""
    # GIVEN a store containing cases that have not been analyzed and at least one case is in progress
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    for case in cases_query.all():
        case.analyses = []
        case.action = CaseActions.ANALYZE

    # WHEN filtering cases for cases that have not been analyzed
    filtered_cases: Query = filter_cases_not_analysed(cases=cases_query)

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_cases_by_workflow_search_no_matching_workflow(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases are returned when there are no cases with matching workflow search."""
    # GIVEN a store containing cases with different workflow names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    workflow_search = "non_existent_pipeline"

    # WHEN filtering cases by a non-matching workflow search
    filtered_cases: Query = filter_cases_by_workflow_search(
        cases=cases_query, workflow_search=workflow_search
    )

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_cases_by_workflow_search_partial_match(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that cases with partially matching workflow search are returned."""
    # GIVEN a store containing cases with different workflow names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    workflow_search = cases_query.first().data_analysis[:3]

    # WHEN filtering cases by a partially matching workflow search
    filtered_cases: Query = filter_cases_by_workflow_search(
        cases=cases_query, workflow_search=workflow_search
    )

    # THEN the query should return the cases with partially matching workflow names
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert workflow_search in case.data_analysis


def test_filter_cases_by_workflow_search_exact_match(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that cases with exactly matching workflow search are returned."""
    # GIVEN a store containing cases with different workflow names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    workflow_search = cases_query.first().data_analysis

    # WHEN filtering cases by an exactly matching workflow search
    filtered_cases: Query = filter_cases_by_workflow_search(
        cases=cases_query, workflow_search=workflow_search
    )

    # THEN the query should return the cases with exactly matching workflow names
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert case.data_analysis == workflow_search


def test_filter_cases_by_priority_no_matching_priority(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases are returned when there are no cases with matching priority."""
    # GIVEN a store containing cases with different priorities
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    non_existent_priority = "non_existent_priority"

    # WHEN filtering cases by a non-matching priority
    filtered_cases: Query = filter_cases_by_priority(
        cases=cases_query, priority=non_existent_priority
    )

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_cases_by_priority_matching_priority(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that cases with matching priority are returned."""
    # GIVEN a store containing cases with different priorities
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    existing_priority = cases_query.first().priority

    # WHEN filtering cases by a matching priority
    filtered_cases: Query = filter_cases_by_priority(cases=cases_query, priority=existing_priority)

    # THEN the query should return the cases with matching priority
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert case.priority == existing_priority


def test_filter_cases_by_priority_all_priorities(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that filtering cases by all available priorities returns all cases."""
    # GIVEN a store containing cases with different priorities
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    all_priorities = {case.priority for case in cases_query}

    # WHEN filtering cases by all available priorities
    filtered_cases = []
    for priority in all_priorities:
        filtered_cases.extend(filter_cases_by_priority(cases=cases_query, priority=priority).all())

    # THEN the query should return all cases
    assert len(filtered_cases) == cases_query.count()


def test_filter_newer_cases_by_order_date_no_newer_cases(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases are returned when there are no cases with a newer order date."""
    # GIVEN a store containing cases with different order dates
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    latest_order_date = max(case.ordered_at for case in cases_query)

    # WHEN filtering cases by a date that is later than the latest order date
    filtered_cases: Query = filter_newer_cases_by_order_date(
        cases=cases_query, order_date=latest_order_date
    )

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_newer_cases_by_order_date_some_newer_cases(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that cases with order dates newer than the given date are returned."""
    # GIVEN a store containing cases with different order dates
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    min_order_date = min(case.ordered_at for case in cases_query)
    max_order_date = max(case.ordered_at for case in cases_query)

    # GIVEN an intermediate date between the minimum and maximum order dates
    intermediate_order_date = min_order_date + (max_order_date - min_order_date) / 2

    # WHEN filtering cases by a date that is earlier than some order dates
    filtered_cases: Query = filter_newer_cases_by_order_date(
        cases=cases_query, order_date=intermediate_order_date
    )

    # THEN the query should return the cases with order dates newer than the given date
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert case.ordered_at > intermediate_order_date


def test_get_older_cases_by_created_date_no_older_cases(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases are returned when there are no cases with an older creation date."""
    # GIVEN a store containing cases with different creation dates
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    oldest_created_date = min(case.created_at for case in cases_query)

    # WHEN filtering cases by a date that is later than the oldest order date
    filtered_cases: Query = filter_older_cases_by_creation_date(
        cases=cases_query, creation_date=oldest_created_date
    )

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_runningfilter_older_cases_by_creation_date_some_newer_cases(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that cases with creation dates older than the given date are returned."""
    # GIVEN a store containing cases with different creation dates
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Case)
    min_creation_date = min(case.created_at for case in cases_query)
    max_creation_date = max(case.created_at for case in cases_query)

    # GIVEN an intermediate date between the minimum and maximum creation dates
    intermediate_creation_date = min_creation_date + (max_creation_date - min_creation_date) / 2

    # WHEN filtering cases by a date that is earlier than some creation dates
    filtered_cases: Query = filter_older_cases_by_creation_date(
        cases=cases_query, creation_date=intermediate_creation_date
    )

    # THEN the query should return the cases with creation dates older than the given date
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert case.created_at < intermediate_creation_date
