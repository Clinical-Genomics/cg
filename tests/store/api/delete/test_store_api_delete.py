from cg.store import Store
from cg.store.models import Flowcell, Family, FamilySample


def test_store_api_delete_flowcell(flow_cell_id: str, populated_flow_cell_store: Store):
    """Test function to delete a flow cell entry in Store"""

    # GIVEN a database containing a flow cell
    flow_cell: Flowcell = populated_flow_cell_store.get_flow_cell(flow_cell_id=flow_cell_id)

    assert flow_cell

    # WHEN removing said flow cell
    populated_flow_cell_store.delete_flowcell(flowcell_name=flow_cell_id)

    # THEN no entry should be found for said flow cell
    results: Flowcell = populated_flow_cell_store.get_flow_cell(flow_cell_id=flow_cell_id)

    assert not results


def test_store_api_delete_relationships_between_sample_and_cases(
    sample_id_in_single_case: str, sample_id_in_multiple_cases: str, dummy_store: Store
):
    """Test function to delete association between a sample and a case in store."""

    # GIVEN a store containing multiple samples associated with different cases
    sample_in_single_case = dummy_store.sample(internal_id=sample_id_in_single_case)
    sample_in_multiple_cases = dummy_store.sample(internal_id=sample_id_in_multiple_cases)

    assert sample_in_single_case
    assert sample_in_multiple_cases

    # WHEN removing the relationships between one sample and its cases
    dummy_store.delete_relationships_sample(sample=sample_in_single_case)

    # THEN it should no longer be associated with any cases, but other relationships should remain
    results = dummy_store.get_cases_from_sample(sample_entry_id=sample_in_single_case.id)
    existing_relationships = dummy_store.get_cases_from_sample(
        sample_entry_id=sample_in_multiple_cases.id
    )

    assert not results
    assert existing_relationships


def test_store_api_delete_all_empty_cases(
    case_id_without_samples: str, case_id_with_multiple_samples: str, dummy_store: Store
):
    """Test function to delete cases that are not associated with any samples"""

    # GIVEN a database containing a case without samples and a case with samples
    case_without_samples = dummy_store.family_samples(case_id_without_samples)
    case_with_samples = dummy_store.family_samples(case_id_with_multiple_samples)

    assert not case_without_samples
    assert case_with_samples

    # WHEN removing empty cases
    dummy_store.delete_cases_without_samples(
        [case_id_without_samples, case_id_with_multiple_samples]
    )

    # THEN no entry should be found for the empty case, but the one with samples should remain.
    result = dummy_store.family_samples(case_id_without_samples)
    case_with_samples = dummy_store.family_samples(case_id_with_multiple_samples)

    assert not result
    assert case_with_samples

def test_store_api_delete_non_existing_case(dummy_store: Store):
    """Test that nothing happens when trying to delete a case that does not exist."""

    # GIVEN a database containing some cases but not a specific case
    case_id = "some_case"
    case = dummy_store.family(case_id)
    existing_cases = dummy_store.families().all()

    assert not case
    assert existing_cases

    # WHEN removing empty cases, specifying the non existing case
    dummy_store.delete_cases_without_samples(case_ids=[case_id])

    # THEN no case has been deleted and nothing happens
    remaining_cases = dummy_store.families().all()

    assert len(remaining_cases) == len(existing_cases)
