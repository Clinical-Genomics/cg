"""Fixtures for meta/upload tests."""

from datetime import datetime

import pytest

from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def analysis(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers: StoreHelpers
) -> Analysis:
    """Return an analysis object with a trio."""
    case_obj = analysis_store_trio.get_case_by_internal_id(internal_id=case_id)
    helpers.add_analysis(store=analysis_store_trio, case=case_obj, started_at=timestamp)
    return analysis_store_trio.get_case_by_internal_id(internal_id=case_id).analyses[0]


@pytest.fixture(name="mip_dna_case")
def mip_dna_case(mip_dna_context: CGConfig, helpers: StoreHelpers) -> Case:
    """Return a MIP DNA case."""

    store: Store = mip_dna_context.status_db

    mip_dna_case: Case = helpers.add_case(
        store=store,
        internal_id="mip-dna-case",
        name="mip-dna-case",
        data_analysis=Workflow.MIP_DNA,
    )
    dna_mip_sample: Sample = helpers.add_sample(
        store=store, application_type="wgs", internal_id="mip-dna-case"
    )
    helpers.add_relationship(store=store, case=mip_dna_case, sample=dna_mip_sample)

    helpers.add_analysis(store=store, case=mip_dna_case, workflow=Workflow.MIP_DNA)

    return mip_dna_case


@pytest.fixture(name="mip_rna_case")
def mip_rna_case(mip_rna_context: CGConfig, case_id: str):
    """Return a MIP RNA case."""
    return mip_rna_context.status_db.get_case_by_internal_id(internal_id=case_id)


@pytest.fixture(name="mip_rna_analysis")
def mip_rna_analysis(mip_rna_context: CGConfig, helpers: StoreHelpers, mip_rna_case: Case) -> Case:
    """Return a MIP RNA analysis."""
    return helpers.add_analysis(
        store=mip_rna_context.status_db, case=mip_rna_case, workflow=Workflow.MIP_RNA
    )
