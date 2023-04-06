from typing import List

from sqlalchemy.orm import Query

from datetime import datetime

from cg.store import Store
from cg.store.models import Family, Sample, FamilySample
from cg.store.filters.status_case_sample_filters import (
    get_samples_associated_with_case_by_case_id,
    get_cases_associated_with_sample_by_entry_id,
)
from tests.store_helpers import StoreHelpers


def test_get_samples_associated_with_case_by_case_id_valid_id(store_with_analyses_for_cases: Store):
    """Test that the case id of the filtered case-sample is the correct one."""
    # GIVEN a store with case-samples
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()
    assert case_sample_query.count() > 0
    # GIVEN a case_id from the store
    case_internal_id: str = case_sample_query.first().family.internal_id
    assert case_internal_id

    # WHEN filtering by the chosen case id
    filtered_query: Query = get_samples_associated_with_case_by_case_id(
        case_samples=case_sample_query, case_id=case_internal_id
    )

    # THEN the filtered query has fewer elements than the original query
    assert filtered_query.count() < case_sample_query.count()
    # THEN the case_samples in the filtered query have the correct case id
    assert all(
        case_sample.family.internal_id == case_internal_id for case_sample in filtered_query.all()
    )


def test_get_samples_associated_with_case_by_case_id_unexistent_id(
    store_with_analyses_for_cases: Store, case_id_does_not_exist: str
):
    """Test that an empty query is returned when filtering using an unexistent case id."""
    # GIVEN a store with case-samples
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()
    assert case_sample_query.count() > 0

    # WHEN filtering using an unexistent id
    filtered_query: Query = get_samples_associated_with_case_by_case_id(
        case_samples=case_sample_query, case_id=case_id_does_not_exist
    )

    # THEN the filtered query is empty
    assert filtered_query.count() == 0


def test_get_cases_associated_with_sample_by_entry_id_valid_id(
    store_with_analyses_for_cases: Store,
):
    """Test that filtering by a valid entry id returns case-samples with the desired entry id."""
    # GIVEN a store with case-samples
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()
    assert case_sample_query.count() > 0
    # GIVEN one sample entry id in the store
    sample_entry_id: int = case_sample_query.first().sample_id
    assert sample_entry_id

    # WHEN filtering the query by the chosen sample entry id
    filtered_query: Query = get_cases_associated_with_sample_by_entry_id(
        case_samples=case_sample_query, sample_entry_id=sample_entry_id
    )

    # THEN the filtered query has fewer elements than the original query
    assert filtered_query.count() < case_sample_query.count()
    # THEN the case_samples in the filtered query have the correct case id
    assert all(case_sample.sample_id == sample_entry_id for case_sample in filtered_query.all())


def test_get_cases_associated_with_sample_by_entry_id_invalid_id(
    store_with_analyses_for_cases: Store,
    invalid_entry_id: int = -1,
):
    """Test that filtering with an invalid entry id returns an empty query."""
    # GIVEN a store with case-samples
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()
    assert case_sample_query.count() > 0

    # WHEN filtering using an invalid entry id
    filtered_query: Query = get_cases_associated_with_sample_by_entry_id(
        case_samples=case_sample_query, sample_entry_id=invalid_entry_id
    )

    # THEN the filtered query is empty
    assert filtered_query.count() == 0
