"""Tests the findbusinessdata part of the cg.store.api"""
from datetime import datetime

import pytest
from cgmodels.cg.constants import Pipeline

from cg.store import Store, models
from tests.store_helpers import StoreHelpers


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
    [Pipeline.BALSAMIC, Pipeline.MIP_DNA],
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
