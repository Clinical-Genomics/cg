"""Tests the findbusinessdata part of the Cg store API related to the Family model."""
from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants.constants import CaseActions
from cg.store import Store
from cg.store.models import (
    Family,
)


def test_get_cases_by_customer_and_case_name_search(store_with_cases_and_customers: Store):
    """Test that only cases with the specified customer and case name search pattern are returned."""
    # GIVEN a store with some cases and customers
    case = store_with_cases_and_customers._get_query(table=Family).first()
    case_name_search = case.name[:3]
    customer = case.customer

    # WHEN calling filtering with the customer and case_name_search
    filtered_cases = store_with_cases_and_customers.get_cases_by_customer_and_case_name_search(
        customer=customer, case_name_search=case_name_search
    )

    # THEN cases with the specified customer and case name search pattern should be returned
    for case in filtered_cases:
        assert case_name_search in case.name
        assert case.customer == customer


def test_get_cases_by_customers_action_and_case_search_pattern(
    store_with_cases_and_customers: Store,
):
    """Test that only cases with the specified customers, action, and case search pattern are returned."""
    # GIVEN a store with some cases and customers
    case = store_with_cases_and_customers._get_query(table=Family).first()
    customer = case.customer
    assert case, customer

    action = case.action
    case_search = case.name[:3]

    # WHEN calling get_cases_by_customers_action_and_case_search_pattern with customers, action, and case_search
    cases = store_with_cases_and_customers.get_cases_by_customers_action_and_case_search(
        customers=[customer], action=action, case_search=case_search
    )

    # THEN cases with the specified customers, action, and case search pattern should be returned
    for case in cases:
        assert case.customer == customer
        assert case.action == action
        assert case_search in case.name


def test_get_cases_by_customer_pipeline_and_case_search_pattern(
    store_with_cases_and_customers: Store,
):
    """Test that only cases with the specified customer, pipeline, and case search pattern are returned."""
    # GIVEN a store with some cases and customers
    case = store_with_cases_and_customers._get_query(table=Family).first()

    # Set the pipeline and case_search
    customer = case.customer
    pipeline = case.data_analysis
    case_search = case.name[:3]

    # WHEN calling get_cases_by_customer_pipeline_and_case_search_pattern with customer, pipeline, and case_search
    cases = store_with_cases_and_customers.get_cases_by_customer_pipeline_and_case_search(
        customer=customer, pipeline=pipeline, case_search=case_search
    )

    # THEN cases with the specified customer, pipeline, and case search pattern should be returned
    for case in cases:
        assert case.customer == customer
        assert case.data_analysis == pipeline
        assert case_search in case.name


def test_get_running_cases_in_pipeline(store_with_cases_and_customers: Store):
    """Test that only cases with the specified pipeline, and have action "running" are returned."""
    # GIVEN a store with some cases

    # WHEN getting cases with a pipeline and are running
    cases: List[Family] = store_with_cases_and_customers.get_running_cases_in_pipeline(
        pipeline=Pipeline.MIP_DNA
    )

    # THEN cases with the specified pipeline, and case action is returned
    for case in cases:
        assert case.action == CaseActions.RUNNING
        assert case.data_analysis == Pipeline.MIP_DNA
