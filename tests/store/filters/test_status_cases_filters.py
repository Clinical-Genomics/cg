from typing import List, Union

from sqlalchemy.orm import Query
from cgmodels.cg.constants import Pipeline
from datetime import datetime

from cg.constants.constants import CaseActions, DataDelivery
from cg.constants.sequencing import SequencingMethod
from cg.constants.subject import PhenotypeStatus
from cg.store import Store
from cg.store.filters.status_case_filters import (
    filter_case_by_internal_id,
    filter_cases_by_case_search,
    filter_cases_by_customer_entry_ids,
    filter_cases_by_entry_id,
    filter_cases_by_name,
    filter_cases_by_pipeline_search,
    filter_cases_by_priority,
    filter_cases_by_ticket_id,
    filter_cases_for_analysis,
    filter_cases_has_sequence,
    filter_cases_not_analysed,
    filter_cases_with_loqusdb_supported_pipeline,
    filter_cases_with_loqusdb_supported_sequencing_method,
    filter_cases_with_pipeline,
    filter_cases_with_scout_data_delivery,
    filter_inactive_analysis_cases,
    filter_newer_cases_by_order_date,
    filter_older_cases_by_creation_date,
    filter_report_supported_data_delivery_cases,
    filter_running_cases,
)
from cg.store.models import Analysis, Family, Sample
from tests.store_helpers import StoreHelpers


def test_filter_cases_has_sequence(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when there is a cases with a sequenced sample."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

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
    test_sample: Sample = helpers.add_sample(base_store, sequenced_at=None, is_external=True)

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse
    cases: Query = filter_cases_has_sequence(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases


def test_filter_cases_has_sequence_when_not_sequenced(base_store: Store, helpers: StoreHelpers):
    """Test that no case is returned when there is a cases with sample that has not been sequenced."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, sequenced_at=None)

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse
    cases: Query = filter_cases_has_sequence(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should not contain the test case
    assert not cases.all()


def test_filter_cases_has_sequence_when_not_external_nor_sequenced(
    base_store: Store, helpers: StoreHelpers
):
    """Test that no case is returned when there is a cases with sample that has not been sequenced nor is external."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, sequenced_at=None, is_external=False)

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse
    cases: Query = filter_cases_has_sequence(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should not contain the test case
    assert not cases.all()


def test_filter_cases_with_pipeline_when_correct_pipline(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that no case is returned when there are no cases with the  specified pipeline."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case = helpers.add_case(base_store, data_analysis=Pipeline.BALSAMIC)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse for another pipeline
    cases: List[Query] = list(filter_cases_with_pipeline(cases=cases, pipeline=Pipeline.BALSAMIC))

    # THEN cases should contain the test case
    assert cases


def test_filter_cases_with_pipeline_when_incorrect_pipline(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that no case is returned when there are no cases with the  specified pipeline."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a cancer case
    test_case: Family = helpers.add_case(base_store, data_analysis=Pipeline.BALSAMIC)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse for another pipeline
    cases: List[Query] = list(filter_cases_with_pipeline(cases=cases, pipeline=Pipeline.MIP_DNA))

    # THEN cases should not contain the test case
    assert not cases


def test_filter_cases_with_loqusdb_supported_pipeline(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test retrieval of cases that support Loqusdb upload."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a MIP-DNA and a FLUFFY case
    test_mip_case: Family = helpers.add_case(base_store, data_analysis=Pipeline.MIP_DNA)
    test_mip_case.customer.loqus_upload = True
    test_fluffy_case: Family = helpers.add_case(
        base_store, name="test", data_analysis=Pipeline.FLUFFY
    )
    test_fluffy_case.customer.loqus_upload = True

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_mip_case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.relate_sample(test_fluffy_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases with pipeline
    cases: List[Query] = list(filter_cases_with_loqusdb_supported_pipeline(cases=cases))

    # THEN only the Loqusdb supported case should be extracted
    assert test_mip_case in cases
    assert test_fluffy_case not in cases


def test_filter_cases_with_loqusdb_supported_sequencing_method(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test retrieval of cases with a valid Loqusdb sequencing method."""

    # GIVEN a sample with a valid Loqusdb sequencing method
    test_sample_wes: Sample = helpers.add_sample(
        base_store, sequenced_at=timestamp_now, application_type=SequencingMethod.WES
    )

    # GIVEN a MIP-DNA associated test case
    test_case_wes: Family = helpers.add_case(base_store, data_analysis=Pipeline.MIP_DNA)
    base_store.relate_sample(test_case_wes, test_sample_wes, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN retrieving the available cases
    cases: Query = filter_cases_with_loqusdb_supported_sequencing_method(
        cases=cases, pipeline=Pipeline.MIP_DNA
    )

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN the expected case should be retrieved
    assert test_case_wes in cases


def test_filter_cases_with_loqusdb_supported_sequencing_method_empty(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test retrieval of cases with a valid Loqusdb sequencing method."""

    # GIVEN a not supported loqusdb sample
    test_sample_wts: Sample = helpers.add_sample(
        base_store, name="sample_wts", sequenced_at=timestamp_now, is_rna=True
    )

    # GIVEN a MIP-DNA associated test case
    test_case_wts: Family = helpers.add_case(base_store, data_analysis=Pipeline.MIP_DNA)
    base_store.relate_sample(test_case_wts, test_sample_wts, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN retrieving the valid cases
    cases: Query = filter_cases_with_loqusdb_supported_sequencing_method(
        cases=cases, pipeline=Pipeline.MIP_DNA
    )

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN no cases should be returned
    assert not cases.all()


def test_filter_cases_for_analysis(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when there is a cases with an action set to analyse."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(
        base_store, completed_at=timestamp_now, pipeline=Pipeline.MIP_DNA
    )

    # Given an action set to analyze
    test_analysis.family.action: str = CaseActions.ANALYZE

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases


def test_filter_cases_for_analysis_when_sequenced_sample_and_no_analysis(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when there are internally created cases with no action set and no prior analysis."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(
        base_store, sequenced_at=timestamp_now, is_external=False
    )

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases


def test_filter_cases_for_analysis_when_cases_with_no_action_and_new_sequence_data(
    base_store: Store,
    helpers: StoreHelpers,
    timestamp_yesterday: datetime,
    timestamp_now: datetime,
):
    """Test that a case is returned when cases with no action, but new sequence data."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(
        base_store, sequenced_at=timestamp_now, is_external=False
    )

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(base_store, pipeline=Pipeline.MIP_DNA)

    # Given an action set to None
    test_analysis.family.action: Union[None, str] = None

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN an old analysis
    test_analysis.created_at = timestamp_yesterday

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases


def test_filter_cases_for_analysis_when_cases_with_no_action_and_old_sequence_data(
    base_store: Store, helpers: StoreHelpers, timestamp_yesterday: datetime
):
    """Test that a case is not returned when cases with no action, but old sequence data."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(
        base_store, sequenced_at=timestamp_yesterday, is_external=True
    )

    # GIVEN a completed analysis
    test_analysis: Analysis = helpers.add_analysis(base_store, pipeline=Pipeline.MIP_DNA)

    # Given an action set to None
    test_analysis.family.action: Union[None, str] = None

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_analysis.family, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases to analyse
    cases: Query = filter_cases_for_analysis(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should not contain the test case
    assert not cases.all()


def test_filter_cases_with_scout_data_delivery(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned when Scout is specified as a data delivery option."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store)

    # GIVEN a case with Scout as data delivery
    test_case = helpers.add_case(base_store, data_delivery=DataDelivery.FASTQ_ANALYSIS_SCOUT)

    # GIVEN a database with a case with one sequenced samples for specified analysis
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)

    # GIVEN a cases Query
    cases: Query = base_store._get_outer_join_cases_with_analyses_query()

    # WHEN getting cases with Scout as data delivery option
    cases: Query = filter_cases_with_scout_data_delivery(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases


def test_filter_report_supported_data_delivery_cases(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a case is returned for a delivery report supported data delivery option."""

    # GIVEN a sequenced sample
    test_sample: Sample = helpers.add_sample(base_store)

    # GIVEN a case with Scout and a not supported option as data deliveries
    test_case = helpers.add_case(base_store, data_delivery=DataDelivery.FASTQ_ANALYSIS_SCOUT)
    test_invalid_case = helpers.add_case(base_store, name="test", data_delivery=DataDelivery.FASTQ)

    # GIVEN a database with the test cases
    base_store.relate_sample(test_case, test_sample, PhenotypeStatus.UNKNOWN)
    base_store.relate_sample(test_invalid_case, test_sample, PhenotypeStatus.UNKNOWN)

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
    """Test that an inactive case is returned when there is case which has no action set."""

    # GIVEN a case
    test_case = helpers.add_case(base_store)

    # GIVEN a cases Query
    cases: Query = base_store._get_query(table=Family)

    # WHEN getting completed cases
    cases: Query = filter_inactive_analysis_cases(cases=cases)

    # ASSERT that cases is a query
    assert isinstance(cases, Query)

    # THEN cases should contain the test case
    assert cases

    assert cases.all()[0].internal_id == test_case.internal_id


def test_filter_inactive_analysis_cases_when_on_hold(base_store: Store, helpers: StoreHelpers):
    """Test that an inactivated case is returned when there is case which has action set to hold."""

    # GIVEN a case
    test_case = helpers.add_case(base_store, action=CaseActions.HOLD)

    # GIVEN a cases Query
    cases: Query = base_store._get_query(table=Family)

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
    """Test that no case is returned when there is case which action set to running."""

    # GIVEN a case
    helpers.add_case(base_store, action=CaseActions.RUNNING)

    # GIVEN a cases Query
    cases: Query = base_store._get_query(table=Family)

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
    cases: Query = base_store._get_query(table=Family)

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
    cases: Query = base_store._get_query(table=Family)

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
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
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
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    entry_ids = [case.id for case in cases_query.all()]
    assert non_existent_id not in entry_ids

    # WHEN filtering for cases with the non existing entry id
    cases: Query = filter_cases_by_entry_id(cases=cases_query, entry_id=non_existent_id)

    # THEN the query should contain no cases
    assert cases.count() == 0


def test_filter_case_by_existing_internal_id(
    store_with_multiple_cases_and_samples: Store, case_id: str
):
    # GIVEN a store containing a case with an internal id case_id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    internal_ids = [case.internal_id for case in cases_query.all()]
    assert case_id in internal_ids

    # WHEN filtering for cases with the internal id case_id
    cases: Query = filter_case_by_internal_id(cases=cases_query, internal_id=case_id)

    # THEN the query should contain only one case
    assert cases.count() == 1

    # THEN the case should have the internal id case_id
    assert cases.first().internal_id == case_id


def test_filter_cases_by_non_existing_internal_id(
    store_with_multiple_cases_and_samples: Store, non_existent_id: str
):
    # GIVEN a store containing a case with an internal id case_id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    internal_ids = [case.internal_id for case in cases_query.all()]
    assert non_existent_id not in internal_ids

    # WHEN filtering for cases with the internal id case_id
    cases: Query = filter_case_by_internal_id(cases=cases_query, internal_id=non_existent_id)

    # THEN the query should contain no cases
    assert cases.count() == 0


def test_filter_case_by_empty_internal_id(store_with_multiple_cases_and_samples: Store):
    # GIVEN a store containing cases
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)

    # WHEN filtering for cases with an empty internal id
    cases: Query = filter_case_by_internal_id(cases=cases_query, internal_id="")

    # THEN the query should return no cases
    assert cases.count() == 0


def test_filter_running_cases_no_running_cases(store_with_multiple_cases_and_samples: Store):
    """Test that no cases are returned when no cases have a running action."""
    # GIVEN a store containing cases with no "running" action
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    cases_query = cases_query.filter(Family.action != CaseActions.RUNNING)

    # WHEN getting active cases
    active_cases: Query = filter_running_cases(cases=cases_query)

    # THEN the query should return no cases
    assert active_cases.count() == 0


def test_filter_running_cases_with_running_cases(store_with_multiple_cases_and_samples: Store):
    """Test that at least one case is returned when at least one case has a running action."""
    # GIVEN a store containing cases with at least one "running" action
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    actions: List[str] = [case.action for case in cases_query.all()]
    assert CaseActions.RUNNING in actions

    # WHEN getting active cases
    active_cases: Query = filter_running_cases(cases=cases_query)

    # THEN the query should return at least one case
    assert active_cases.count() >= 1


def test_filter_running_cases_only_running_cases(store_with_multiple_cases_and_samples: Store):
    """Test that all cases are returned when all cases have a running action."""
    # GIVEN a store containing only cases with "running" action
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    for case in cases_query.all():
        case.action = CaseActions.RUNNING

    # WHEN getting active cases
    active_cases: Query = filter_running_cases(cases=cases_query)

    # THEN the query should return the same number of cases as the original query
    assert active_cases.count() == cases_query.count()


def test_filter_cases_by_ticket_no_matching_ticket(
    store_with_multiple_cases_and_samples: Store, non_existent_id: str
):
    """Test that no cases are returned when filtering by a non-existent ticket."""
    # GIVEN a store containing cases with no matching ticket id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)

    # WHEN filtering cases by a non-existent ticket
    filtered_cases: Query = filter_cases_by_ticket_id(cases=cases_query, ticket_id=non_existent_id)

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_cases_by_ticket_matching_ticket(
    store_with_multiple_cases_and_samples: Store, ticket_id: str
):
    """Test that cases are returned when filtering by an existing ticket id."""
    # GIVEN a store containing cases with a matching ticket id
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)

    # WHEN filtering cases by an existing ticket id
    filtered_cases: Query = filter_cases_by_ticket_id(cases=cases_query, ticket_id=ticket_id)

    # THEN the query should return cases with the matching ticket
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert ticket_id in case.tickets


def test_filter_cases_by_customer_entry_ids(store_with_multiple_cases_and_samples: Store):
    """Test that cases are returned when filtering by customer entry ids."""
    # GIVEN a store containing cases with customer ids
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    customer_ids = [case.customer_id for case in cases_query.all()]
    assert customer_ids

    # WHEN filtering cases by customer ids
    filtered_cases: Query = filter_cases_by_customer_entry_ids(
        cases=cases_query, customer_entry_ids=customer_ids
    )

    # THEN the filtered_cases should have the same count as cases_query
    assert filtered_cases.count() == cases_query.count()

    # THEN all cases in filtered_cases should have a customer_id in the customer_ids list
    for case in filtered_cases:
        assert case.customer_id in customer_ids


def test_filter_cases_by_name(store_with_multiple_cases_and_samples: Store):
    """Test that cases are returned when filtering by name."""
    # GIVEN a store containing cases with various names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    test_name = cases_query.first().name

    # WHEN filtering cases by a specific name
    filtered_cases: Query = filter_cases_by_name(cases=cases_query, name=test_name)

    # THEN all cases in filtered_cases should have the specified name
    for case in filtered_cases:
        assert case.name == test_name


def test_filter_cases_by_search_pattern(store_with_multiple_cases_and_samples: Store):
    """Test that cases are returned when filtering by matching internal ids."""
    # GIVEN a store containing cases with internal ids and names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
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
    """Test that no cases are returned when all cases have been analysed."""
    # GIVEN a store containing only cases that have been analysed
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    for case in cases_query.all():
        case.analyses.append(Analysis(completed_at=datetime.now()))

    # WHEN filtering cases for cases that have not been analysed
    filtered_cases: Query = filter_cases_not_analysed(cases=cases_query)

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_cases_not_analysed_no_cases_in_progress(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that all cases are returned when no cases are in progress."""
    # GIVEN a store containing cases that have not been analysed and no cases are in progress
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    for case in cases_query.all():
        case.analyses = []
        case.action = CaseActions.HOLD

    # WHEN filtering cases for cases that have not been analysed
    filtered_cases: Query = filter_cases_not_analysed(cases=cases_query)

    # THEN the query should return all cases
    assert filtered_cases.count() == cases_query.count()


def test_filter_cases_not_analysed_in_progress(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases in progress are returned."""
    # GIVEN a store containing cases that have not been analysed and at least one case is in progress
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    for case in cases_query.all():
        case.analyses = []
        case.action = CaseActions.ANALYZE

    # WHEN filtering cases for cases that have not been analysed
    filtered_cases: Query = filter_cases_not_analysed(cases=cases_query)

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_cases_by_pipeline_search_no_matching_pipeline(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases are returned when there are no cases with matching pipeline search."""
    # GIVEN a store containing cases with different pipeline names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    pipeline_search = "non_existent_pipeline"

    # WHEN filtering cases by a non-matching pipeline search
    filtered_cases: Query = filter_cases_by_pipeline_search(
        cases=cases_query, pipeline_search=pipeline_search
    )

    # THEN the query should return no cases
    assert filtered_cases.count() == 0


def test_filter_cases_by_pipeline_search_partial_match(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that cases with partially matching pipeline search are returned."""
    # GIVEN a store containing cases with different pipeline names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    pipeline_search = cases_query.first().data_analysis[:3]

    # WHEN filtering cases by a partially matching pipeline search
    filtered_cases: Query = filter_cases_by_pipeline_search(
        cases=cases_query, pipeline_search=pipeline_search
    )

    # THEN the query should return the cases with partially matching pipeline names
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert pipeline_search in case.data_analysis


def test_filter_cases_by_pipeline_search_exact_match(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that cases with exactly matching pipeline search are returned."""
    # GIVEN a store containing cases with different pipeline names
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    pipeline_search = cases_query.first().data_analysis

    # WHEN filtering cases by an exactly matching pipeline search
    filtered_cases: Query = filter_cases_by_pipeline_search(
        cases=cases_query, pipeline_search=pipeline_search
    )

    # THEN the query should return the cases with exactly matching pipeline names
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert case.data_analysis == pipeline_search


def test_filter_cases_by_priority_no_matching_priority(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases are returned when there are no cases with matching priority."""
    # GIVEN a store containing cases with different priorities
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
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
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
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
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    all_priorities = set(case.priority for case in cases_query)

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
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
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
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    min_order_date = min(case.ordered_at for case in cases_query)
    max_order_date = max(case.ordered_at for case in cases_query)

    # Calculate an intermediate date between the minimum and maximum order dates
    some_order_date = min_order_date + (max_order_date - min_order_date) / 2

    # WHEN filtering cases by a date that is earlier than some order dates
    filtered_cases: Query = filter_newer_cases_by_order_date(
        cases=cases_query, order_date=some_order_date
    )

    # THEN the query should return the cases with order dates newer than the given date
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert case.ordered_at > some_order_date


def test_get_older_cases_by_created_date_no_older_cases(
    store_with_multiple_cases_and_samples: Store,
):
    """Test that no cases are returned when there are no cases with an older creation date."""
    # GIVEN a store containing cases with different creation dates
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
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
    cases_query: Query = store_with_multiple_cases_and_samples._get_query(table=Family)
    min_creation_date = min(case.created_at for case in cases_query)
    max_creation_date = max(case.created_at for case in cases_query)

    # Calculate an intermediate date between the minimum and maximum creation dates
    some_creation_date = min_creation_date + (max_creation_date - min_creation_date) / 2

    # WHEN filtering cases by a date that is earlier than some creation dates
    filtered_cases: Query = filter_older_cases_by_creation_date(
        cases=cases_query, creation_date=some_creation_date
    )

    # THEN the query should return the cases with creation dates older than the given date
    assert filtered_cases.count() > 0
    for case in filtered_cases:
        assert case.created_at < some_creation_date
