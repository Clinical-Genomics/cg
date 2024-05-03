from cg.store.models import Case, CaseSample, Flowcell, Sample
from cg.store.store import Store
from tests.meta.demultiplex.conftest import populated_flow_cell_store


def test_delete_flow_cell(
    novaseq_6000_pre_1_5_kits_flow_cell_id: str, populated_flow_cell_store: Store
):
    """Test deleting a flow cell in Store."""

    # GIVEN a database containing a flow cell
    flow_cell: Flowcell = populated_flow_cell_store.get_flow_cell_by_name(
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id
    )

    assert flow_cell

    # WHEN removing flow cell
    populated_flow_cell_store.delete_flow_cell(flow_cell_id=novaseq_6000_pre_1_5_kits_flow_cell_id)

    # THEN no entry should be found for the flow cell
    results: Flowcell = populated_flow_cell_store.get_flow_cell_by_name(
        flow_cell_name=novaseq_6000_pre_1_5_kits_flow_cell_id
    )

    assert not results


def test_store_api_delete_relationships_between_sample_and_cases(
    sample_id_in_single_case: str,
    sample_id_in_multiple_cases: str,
    store_with_multiple_cases_and_samples: Store,
):
    """Test function to delete association between a sample and a case in store."""

    # GIVEN a store containing multiple samples associated with different cases
    sample_in_single_case: Sample = store_with_multiple_cases_and_samples.get_sample_by_internal_id(
        internal_id=sample_id_in_single_case
    )
    sample_in_multiple_cases: Sample = (
        store_with_multiple_cases_and_samples.get_sample_by_internal_id(
            internal_id=sample_id_in_multiple_cases
        )
    )

    assert sample_in_single_case
    assert sample_in_multiple_cases

    # WHEN removing the relationships between one sample and its cases
    store_with_multiple_cases_and_samples.delete_relationships_sample(sample=sample_in_single_case)

    # THEN it should no longer be associated with any cases, but other relationships should remain
    results: list[CaseSample] = (
        store_with_multiple_cases_and_samples._get_query(table=CaseSample)
        .filter(CaseSample.sample_id == sample_in_single_case.id)
        .all()
    )
    existing_relationships: list[CaseSample] = (
        store_with_multiple_cases_and_samples._get_query(table=CaseSample)
        .filter(CaseSample.sample_id == sample_in_multiple_cases.id)
        .all()
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
    case_without_samples: list[CaseSample] = (
        store_with_multiple_cases_and_samples.get_case_samples_by_case_id(
            case_internal_id=case_id_without_samples
        )
    )
    case_with_samples: list[CaseSample] = (
        store_with_multiple_cases_and_samples.get_case_samples_by_case_id(
            case_internal_id=case_id_with_multiple_samples
        )
    )

    assert not case_without_samples
    assert case_with_samples

    # WHEN removing empty cases
    store_with_multiple_cases_and_samples.delete_cases_without_samples(
        [case_id_without_samples, case_id_with_multiple_samples]
    )

    # THEN no entry should be found for the empty case, but the one with samples should remain.
    result: list[CaseSample] = store_with_multiple_cases_and_samples.get_case_samples_by_case_id(
        case_internal_id=case_id_without_samples
    )
    case_with_samples: list[CaseSample] = (
        store_with_multiple_cases_and_samples.get_case_samples_by_case_id(
            case_internal_id=case_id_with_multiple_samples
        )
    )

    assert not result
    assert case_with_samples


def test_store_api_delete_non_existing_case(
    case_id_does_not_exist: str, store_with_multiple_cases_and_samples: Store
):
    """Test that nothing happens when trying to delete a case that does not exist."""

    # GIVEN a database containing some cases but not a specific case
    case: Case = store_with_multiple_cases_and_samples.get_case_by_internal_id(
        internal_id=case_id_does_not_exist
    )
    existing_cases: list[Case] = store_with_multiple_cases_and_samples.get_cases()

    assert not case
    assert existing_cases

    # WHEN removing empty cases, specifying the non existing case
    store_with_multiple_cases_and_samples.delete_cases_without_samples(
        case_internal_ids=[case_id_does_not_exist]
    )

    # THEN no case has been deleted and nothing happens
    remaining_cases: list[Case] = store_with_multiple_cases_and_samples.get_cases()

    assert len(remaining_cases) == len(existing_cases)


def test_delete_flow_cell_entries_in_sample_lane_sequencing_metrics(
    store_with_sequencing_metrics: Store, flow_cell_name: str
):
    """Test function to delete flow cell entries in sample_lane_sequencing_metrics table"""

    # GIVEN a database containing a flow cell
    metrics = store_with_sequencing_metrics.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=flow_cell_name
    )
    assert metrics

    # WHEN removing flow cell
    store_with_sequencing_metrics.delete_flow_cell_entries_in_sample_lane_sequencing_metrics(
        flow_cell_name=metrics[0].flow_cell_name
    )

    # THEN no entry should be found for the flow cell
    assert not store_with_sequencing_metrics.get_sample_lane_sequencing_metrics_by_flow_cell_name(
        flow_cell_name=metrics[0].flow_cell_name
    )
