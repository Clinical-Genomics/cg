"""Tests the findbusinessdata part of the Cg store API related to the Family model."""
from datetime import datetime
from typing import List
from cg.constants.constants import CaseActions
from cg.store import Store
from cg.store.models import (
    Customer,
    Family,
)
from tests.store_helpers import StoreHelpers
from cg.constants import Pipeline


def test_get_filtered_cases_no_filters(store_with_cases_and_customers: Store):
    """Test that all cases are returned when no filters are applied."""
    # GIVEN a store with some cases
    all_cases_query = store_with_cases_and_customers._get_query(table=Family)
    assert all_cases_query.count() > 0

    # WHEN calling get_filtered_cases with no filters
    filtered_cases_query = store_with_cases_and_customers.get_filtered_cases()

    # THEN all cases should be returned
    assert filtered_cases_query.count() == all_cases_query.count()


def test_get_filtered_cases_action_filter(store_with_cases_and_customers: Store):
    """Test that only cases with the specified action are returned."""
    # GIVEN a store with some cases with a specifc action and other cases with other actions
    action: str = CaseActions.RUNNING.value
    all_cases = store_with_cases_and_customers._get_query(table=Family).all()
    all_actions = [case.action for case in all_cases]

    assert action in all_actions and any(other_action != action for other_action in all_actions)

    # WHEN calling get_filtered_cases with action filter
    cases = store_with_cases_and_customers.get_filtered_cases(action=action).all()

    # THEN some cases are returned
    assert cases

    # THEN only cases with the specified action are present
    assert all(case.action == action for case in cases)


def test_get_filtered_cases_pipeline_filter(store_with_cases_and_customers: Store):
    """Test that only cases with the specified pipeline are returned."""
    # GIVEN a store with some cases with a specifc pipeline and other cases with other pipelines
    pipeline: str = Pipeline.BALSAMIC.value
    all_cases = store_with_cases_and_customers._get_query(table=Family).all()
    all_pipelines = [case.data_analysis for case in all_cases]

    assert pipeline in all_pipelines and any(
        other_pipeline != pipeline for other_pipeline in all_pipelines
    )

    # WHEN calling get_filtered_cases with pipeline filter
    cases = store_with_cases_and_customers.get_filtered_cases(pipeline=pipeline).all()

    # THEN some cases are returned
    assert cases

    # THEN only cases with the specified pipeline should be returned
    assert all(case.data_analysis == pipeline for case in cases)


def test_get_filtered_cases_case_internal_id_or_name_search_pattern_filter(
    store_with_cases_and_customers: Store,
):
    """Test that only cases with the specified search pattern in internal_id are returned."""
    # GIVEN a store with some cases
    all_cases = store_with_cases_and_customers._get_query(table=Family).all()
    assert all_cases

    # Extract the internal_ids and names of the cases
    case_internal_ids = [case.internal_id for case in all_cases]

    # Create search patterns by taking a part of the internal_id or name of a case
    internal_id_search_pattern = case_internal_ids[0][:3]

    # WHEN calling get_filtered_cases with case_internal_id_or_name_search_pattern filter
    cases = store_with_cases_and_customers.get_filtered_cases(
        case_internal_id_or_name_search_pattern=internal_id_search_pattern
    ).all()

    # THEN cases with the specified search pattern in internal_id should be returned
    assert all(internal_id_search_pattern in case.internal_id for case in cases)


def test_get_filtered_cases_multiple_filters(store_with_cases_and_customers: Store):
    """Test that only cases that meet all filter criteria are returned."""
    # GIVEN a store with some cases
    all_cases = store_with_cases_and_customers._get_query(table=Family).all()
    assert all_cases

    # Set the filters
    case: Family = all_cases[-1]

    action = case.action
    pipeline = case.data_analysis
    customers = [case.customer]
    internal_id_search_pattern = case.internal_id[:3]

    # WHEN calling get_filtered_cases with multiple filters
    cases = store_with_cases_and_customers.get_filtered_cases(
        action=action,
        pipeline=pipeline,
        customers=customers,
        case_internal_id_or_name_search_pattern=internal_id_search_pattern,
    )

    # THEN only cases that meet all filter criteria should be returned
    for case in cases:
        assert case.action == action
        assert case.data_analysis == pipeline
        assert case.customer in customers
        assert internal_id_search_pattern in case.internal_id
