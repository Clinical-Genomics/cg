from typing import List

from sqlalchemy.orm import Query

from datetime import datetime

from cg.store import Store
from cg.store.models import Family, Sample, FamilySample
from cg.store.filters.status_case_sample_filters import (
    get_samples_associated_with_case,
    get_cases_associated_with_sample_by_entry_id,
)
from tests.store_helpers import StoreHelpers


def test_get_samples_associated_with_case_valid_id(store_with_analyses_for_cases: Store):
    """Test that the case id of the filtered case_sample is the correct one."""
    # GIVEN a store with case_samples
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()
    assert case_sample_query.count() > 0
    # GIVEN a case_id from the store
    case_id: str = case_sample_query.first().family_id
    assert case_id

    # WHEN filtering by the chosen case id
    filtered_query: Query = get_samples_associated_with_case(
        case_samples=case_sample_query, case_id=case_id
    )

    # THEN the filtered query has fewer elements than the original query
    assert filtered_query.count() < case_sample_query.count()
    # THEN the case_samples in the query have the correct case id
    assert all(case_sample.family_id == case_id for case_sample in filtered_query.all())


def test_get_samples_associated_with_case_unexistent_id(
    store_with_analyses_for_cases: Store, case_id_does_not_exist: str
):
    """Test that an empty query is returned when filtering using an unexistent case id."""
    # GIVEN a store with case samples
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()
    assert case_sample_query.count() > 0

    # WHEN filtering using an unexistent id
    filtered_query: Query = get_samples_associated_with_case(
        case_samples=case_sample_query, case_id=case_id_does_not_exist
    )

    # THEN the returned query is empty
    assert filtered_query.count() == 0


def test_get_cases_associated_with_sample_by_entry_id():
    """."""
    # GIVEN

    # WHEN

    # THEN
