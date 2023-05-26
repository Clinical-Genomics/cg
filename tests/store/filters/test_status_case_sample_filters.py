from sqlalchemy.orm import Query

from cg.store import Store
from cg.store.filters.status_case_sample_filters import (
    get_samples_in_case_by_internal_id,
    get_cases_with_sample_by_internal_id,
)


def test_get_samples_in_case_by_internal_id_valid_id(
    store_with_analyses_for_cases: Store,
    case_id: str,
):
    """Test that filtering by a valid case id returns case-samples with the desired case id."""
    # GIVEN a store with case-samples and a case internal id
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()

    # WHEN filtering by the chosen case internal id
    filtered_query: Query = get_samples_in_case_by_internal_id(
        case_samples=case_sample_query, case_internal_id=case_id
    )

    # THEN the filtered query has at least one element but fewer elements than the original query
    assert 0 < filtered_query.count() < case_sample_query.count()
    # THEN the case_samples in the filtered query have the correct case internal id
    for case_sample in filtered_query.all():
        assert case_sample.family.internal_id == case_id


def test_get_samples_in_case_by_internal_id_nonexistent_id(
    store_with_analyses_for_cases: Store, case_id_does_not_exist: str
):
    """Test that an empty query is returned when filtering using a non-existent case id."""
    # GIVEN a store with case-samples and an unexistent case internal id
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()
    assert case_sample_query.count() > 0

    # WHEN filtering using a non-existent id
    filtered_query: Query = get_samples_in_case_by_internal_id(
        case_samples=case_sample_query, case_internal_id=case_id_does_not_exist
    )

    # THEN the filtered query is empty
    assert filtered_query.count() == 0


def test_get_cases_with_sample_by_internal_id_valid_id(
    store_with_analyses_for_cases: Store,
    sample_id: str,
):
    """Test that filtering by a valid sample internal id returns case-samples with the desired sample internal id."""
    # GIVEN a store with case-samples and a sample internal id
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()

    # WHEN filtering using a sample internal id
    filtered_query: Query = get_cases_with_sample_by_internal_id(
        case_samples=case_sample_query, sample_internal_id=sample_id
    )

    # THEN the filtered query has at least one element but fewer elements than the original query
    assert 0 < filtered_query.count() < case_sample_query.count()
    # THEN the case_samples in the filtered query have the correct sample internal id
    for case_sample in filtered_query.all():
        assert case_sample.sample.internal_id == sample_id


def test_get_cases_with_sample_by_internal_id_invalid_id(
    store_with_analyses_for_cases: Store, invalid_sample_id: str
):
    """Test that an empty query is returned when filtering using an invalid sample internal id."""
    # GIVEN a store with case-samples and an invalid sample internal id
    case_sample_query: Query = store_with_analyses_for_cases._get_join_case_sample_query()
    assert case_sample_query.count() > 0

    # WHEN filtering using an invalid sample internal id
    filtered_query: Query = get_cases_with_sample_by_internal_id(
        case_samples=case_sample_query, sample_internal_id=invalid_sample_id
    )

    # THEN the filtered query is empty
    assert filtered_query.count() == 0
