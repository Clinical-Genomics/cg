from typing import List
from cg.store import Store
from cg.store.models import Flowcell, Family, FamilySample, Sample


def test_store_api_delete_flowcell(flow_cell_id: str, populated_flow_cell_store: Store):
    """Test function to delete a flow cell entry in Store"""

    # GIVEN a database containing a flow cell
    flow_cell: Flowcell = populated_flow_cell_store.get_flow_cell(flow_cell_id=flow_cell_id)

    assert flow_cell

    # WHEN removing said flow cell
    populated_flow_cell_store.delete_flow_cell(flow_cell_name=flow_cell_id)

    # THEN no entry should be found for said flow cell
    results: Flowcell = populated_flow_cell_store.get_flow_cell(flow_cell_id=flow_cell_id)

    assert not results


def test_store_api_delete_relationships_between_sample_and_cases(
    sample_id_in_single_case: str,
    sample_id_in_multiple_cases: str,
    store_with_multiple_cases_and_samples: Store,
):
    """Test function to delete association between a sample and a case in store."""

    # GIVEN a store containing multiple samples associated with different cases
    sample_in_single_case: Sample = store_with_multiple_cases_and_samples.sample(
        internal_id=sample_id_in_single_case
    )
    sample_in_multiple_cases: Sample = store_with_multiple_cases_and_samples.sample(
        internal_id=sample_id_in_multiple_cases
    )

    assert sample_in_single_case
    assert sample_in_multiple_cases

    # WHEN removing the relationships between one sample and its cases
    store_with_multiple_cases_and_samples.delete_relationships_sample(sample=sample_in_single_case)

    # THEN it should no longer be associated with any cases, but other relationships should remain
    results: List[FamilySample] = store_with_multiple_cases_and_samples.get_cases_from_sample(
        sample_entry_id=sample_in_single_case.id
    )
    existing_relationships: List[
        FamilySample
    ] = store_with_multiple_cases_and_samples.get_cases_from_sample(
        sample_entry_id=sample_in_multiple_cases.id
    )

    assert not results
    assert existing_relationships


def test_store_api_delete_all_empty_cases(
    case_id_without_samples: str,
    case_id_with_multiple_samples: str,
    store_with_multiple_cases_and_samples: Store,
):
    """Test function to delete cases that are not associated with any samples"""

    # GIVEN a database containing a case without samples and a case with samples
    case_without_samples: List[FamilySample] = store_with_multiple_cases_and_samples.family_samples(
        case_id_without_samples
    )
    case_with_samples: List[FamilySample] = store_with_multiple_cases_and_samples.family_samples(
        case_id_with_multiple_samples
    )

    assert not case_without_samples
    assert case_with_samples

    # WHEN removing empty cases
    store_with_multiple_cases_and_samples.delete_cases_without_samples(
        [case_id_without_samples, case_id_with_multiple_samples]
    )

    # THEN no entry should be found for the empty case, but the one with samples should remain.
    result: List[FamilySample] = store_with_multiple_cases_and_samples.family_samples(
        case_id_without_samples
    )
    case_with_samples: List[FamilySample] = store_with_multiple_cases_and_samples.family_samples(
        case_id_with_multiple_samples
    )

    assert not result
    assert case_with_samples


def test_store_api_delete_non_existing_case(
    case_id_does_not_exist: str, store_with_multiple_cases_and_samples: Store
):
    """Test that nothing happens when trying to delete a case that does not exist."""

    # GIVEN a database containing some cases but not a specific case
    case: Family = store_with_multiple_cases_and_samples.family(case_id_does_not_exist)
    existing_cases: List[Family] = store_with_multiple_cases_and_samples.families().all()

    assert not case
    assert existing_cases

    # WHEN removing empty cases, specifying the non existing case
    store_with_multiple_cases_and_samples.delete_cases_without_samples(
        case_ids=[case_id_does_not_exist]
    )

    # THEN no case has been deleted and nothing happens
    remaining_cases: List[Family] = store_with_multiple_cases_and_samples.families().all()

    assert len(remaining_cases) == len(existing_cases)
