"""Tests the findbusinessdata part of the cg.store.api"""
from datetime import datetime

import pytest

from cg.store import Store, models
from cgmodels.cg.constants import Pipeline
from tests.store_helpers import StoreHelpers
from tests.store.api.conftest import fixture_rml_pool_store


def test_find_analysis_via_date(sample_store: Store, helpers: StoreHelpers):
    # GIVEN a case with an analysis with a startdate in the database
    analysis = helpers.add_analysis(store=sample_store, started_at=datetime.now())
    assert analysis.started_at

    # WHEN getting analysis via case_id and start date
    db_analysis = sample_store.analysis(analysis.family, analysis.started_at)

    # THEN the analysis should have been retrieved
    assert db_analysis == analysis


@pytest.mark.parametrize(
    "data_analysis",
    [Pipeline.BALSAMIC, Pipeline.BALSAMIC_QC, Pipeline.BALSAMIC_UMI, Pipeline.MIP_DNA],
)
def test_families_by_subject_id(
    data_analysis: Pipeline,
    helpers: StoreHelpers,
    sample_store: Store,
):
    """Test that we get a case back for a subject id"""
    # GIVEN connected case exist
    subject_id = "a_subject_id"
    store: Store = sample_store

    rna_sample: models.Sample = helpers.add_sample(store=store, subject_id=subject_id)
    rna_case: models.Family = helpers.add_case(
        store=store, data_analysis=Pipeline.MIP_RNA, name="rna_case"
    )
    helpers.add_relationship(store=store, case=rna_case, sample=rna_sample)
    store.add_commit(rna_case)

    dna_sample: models.Sample = helpers.add_sample(store=store, subject_id=subject_id)
    dna_case: models.Family = helpers.add_case(
        store=store, data_analysis=data_analysis, name="dna_case"
    )
    helpers.add_relationship(store=store, case=dna_case, sample=dna_sample)
    store.add_commit(dna_case)

    customer: models.Customer = dna_case.customer

    # WHEN calling method families_by_subject_id
    all_cases: set[models.Family] = sample_store.families_by_subject_id(
        customer_id=customer.internal_id, subject_id=subject_id
    )

    dna_cases: set[models.Family] = sample_store.families_by_subject_id(
        customer_id=customer.internal_id, subject_id=subject_id, data_analyses=[data_analysis]
    )

    # THEN we got the case as result and another data_analysis not in result
    assert dna_case in all_cases
    assert rna_case in all_cases
    assert dna_case in dna_cases
    assert rna_case not in dna_cases


def test_families_by_subject_id_by_is_tumour(
    helpers: StoreHelpers,
    sample_store: Store,
):
    """Test that we get a case back for a subject id depending on tumour state"""
    # GIVEN we have two cases with same subject_id but different is_tumour
    subject_id = "a_subject_id"
    store: Store = sample_store

    tumour_sample: models.Sample = helpers.add_sample(
        store=store, subject_id=subject_id, is_tumour=True
    )
    tumour_case: models.Family = helpers.add_case(store=store, name="tumour_case")
    helpers.add_relationship(store=store, case=tumour_case, sample=tumour_sample)
    store.add_commit(tumour_case)

    non_tumour_sample: models.Sample = helpers.add_sample(
        store=store, subject_id=subject_id, is_tumour=False
    )
    non_tumour_case: models.Family = helpers.add_case(store=store, name="non_tumour_case")
    helpers.add_relationship(store=store, case=non_tumour_case, sample=non_tumour_sample)
    store.add_commit(non_tumour_case)

    customer: models.Customer = tumour_case.customer

    # WHEN calling method families_by_subject_id
    all_cases: set[models.Family] = sample_store.families_by_subject_id(
        customer_id=customer.internal_id, subject_id=subject_id
    )

    tumour_cases: set[models.Family] = sample_store.families_by_subject_id(
        customer_id=customer.internal_id, subject_id=subject_id, is_tumour=True
    )

    non_tumour_cases: set[models.Family] = sample_store.families_by_subject_id(
        customer_id=customer.internal_id, subject_id=subject_id, is_tumour=False
    )

    # THEN we have one group with both cases independent of is_tumour
    assert tumour_case in all_cases
    assert non_tumour_case in all_cases

    # THEN we have two groups depending on is_tumour
    assert tumour_case in tumour_cases
    assert tumour_case not in non_tumour_cases

    assert non_tumour_case in non_tumour_cases
    assert non_tumour_case not in tumour_cases


def test_get_latest_flow_cell_on_case(
    re_sequenced_sample_store: Store, case_id: str, flowcell_name: str
):
    """Test function to fetch the latest sequenced flowcell on a case"""

    # GIVEN a store with two flow cells in it, one being the latest sequenced of the two
    latest_flow_cell_obj: models.Flowcell = re_sequenced_sample_store.Flowcell.query.filter(
        models.Flowcell.name == flowcell_name
    ).first()

    # WHEN fetching the latest flow cell on a case with a sample that has been sequenced on both flow cells
    latest_flow_cell_on_case: models.Flowcell = (
        re_sequenced_sample_store.get_latest_flow_cell_on_case(family_id=case_id)
    )

    # THEN the fetched flow cell should have the same name as the other
    assert latest_flow_cell_obj.name == latest_flow_cell_on_case.name


def test_get_customer_id_from_ticket(analysis_store, customer_id, ticket: str):
    """Tests if the function in fact returns the correct customer"""
    # Given a store with a ticket

    # Then the function should return the customer connected to the ticket
    assert analysis_store.get_customer_id_from_ticket(ticket) == customer_id


def test_get_latest_ticket_from_case(case_id: str, analysis_store_single_case, ticket: str):
    """Tests if the correct ticket is returned for the given case"""
    # GIVEN a populated store with a case

    # WHEN the function is called
    ticket_from_case: str = analysis_store_single_case.get_latest_ticket_from_case(case_id=case_id)

    # THEN the ticket should be correct
    assert ticket == ticket_from_case


def test_get_case_pool(case_id: str, rml_pool_store: Store):
    """Tests if the correct pool is returned"""
    # GIVEN a case connected to a pool
    case_name = rml_pool_store.family(internal_id=case_id).name
    # WHEN the function is called
    pool = rml_pool_store.get_case_pool(case_id=case_id)
    # THEN the correct pool should be returned and the pool name should be the last part of the
    # case name
    assert pool.name == case_name.split("-", 1)[-1]
