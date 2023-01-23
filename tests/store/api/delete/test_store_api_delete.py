from typing import List
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


def test_store_api_delete_case(case_id: str, rml_pool_store: Store):
    """Test function to delete a case associated with a single sample in Store"""

    # GIVEN a database containing a case
    case: Family = rml_pool_store.family(case_id)

    assert case

    # WHEN removing said case
    rml_pool_store.delete_case(case_id=case_id)

    # THEN no entry should be found for said case
    results: Family = rml_pool_store.family(case_id)

    assert not results


def test_store_api_delete_single_case_sample(sample_id: str, case_id: str, rml_pool_store: Store):
    """Test function to delete association between a sample and a single case given a sample id in Store"""

    # GIVEN a database containing a case associated with a sample
    samples = rml_pool_store.samples().all()
    entry_id = samples[0].id
    case_samples: List[FamilySample] = rml_pool_store.get_cases_from_sample(
        sample_entry_id=entry_id
    )

    assert case_samples

    # WHEN removing said association
    rml_pool_store.delete_case_sample_relationships(sample_entry_id=entry_id)

    # THEN no entry should be found for said association
    results: List[FamilySample] = rml_pool_store.get_cases_from_sample(sample_entry_id=entry_id)

    assert not results


def test_store_api_delete_all_case_samples_for_a_case(case_id: str, rml_pool_store: Store):
    """Test function to delete all associations between a case and its samples given a case id in Store"""

    # GIVEN a database containing a case associated with a sample
    case: Family = rml_pool_store.family(case_id)
    case_samples: FamilySample = rml_pool_store.family_samples(case_id)

    assert case
    assert case_samples != [] and case_samples[0]

    # WHEN removing all relationships between the case and its samples
    rml_pool_store.delete_all_case_sample_relationships(case_id=case_id)

    # THEN no entry should be found for a relationship between the case and a sample.
    results: FamilySample = rml_pool_store.family_samples(case_id)

    assert not results
