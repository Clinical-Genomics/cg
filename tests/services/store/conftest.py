from datetime import datetime

import pytest

from cg.constants import PrepCategory, Workflow
from cg.services.store.rna_dna_collections_service.rna_dna_collections_service import (
    RNADNACollectionsService,
)
from cg.store.models import Case, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def store_with_rna_and_related_dna_sample_and_cases(store: Store, helpers: StoreHelpers) -> Store:
    """Return a store with:
    - 1 rna sample
    - 1 dna sample related to the rna sample
    - 1 more dna sample not related to the dna sample
    - 2 dna cases including the related dna sample"""

    rna_sample: Sample = helpers.add_sample(
        store=store,
        internal_id="rna_sample",
        application_type=PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING.value,
        subject_id="subject_1",
        is_tumour=True,
        customer_id="cust000",
    )
    related_dna_sample: Sample = helpers.add_sample(
        store=store,
        internal_id="related_dna_sample_1",
        application_tag=PrepCategory.WHOLE_GENOME_SEQUENCING.value,
        application_type=PrepCategory.WHOLE_GENOME_SEQUENCING.value,
        subject_id="subject_1",
        is_tumour=True,
        customer_id="cust001",
    )

    helpers.add_sample(
        store=store,
        internal_id="not_related_dna_sample",
        application_tag=PrepCategory.WHOLE_EXOME_SEQUENCING.value,
        application_type=PrepCategory.WHOLE_EXOME_SEQUENCING.value,
        subject_id="subject_2",
        is_tumour=False,
        customer_id="cust000",
    )

    rna_case: Case = helpers.add_case(
        store=store,
        internal_id="rna_case",
        name="rna_case",
        data_analysis=Workflow.MIP_RNA,
        customer_id="cust000",
    )
    helpers.add_relationship(store=store, sample=rna_sample, case=rna_case)

    related_dna_case_1: Case = helpers.add_case(
        store=store,
        internal_id="related_dna_case_1",
        data_analysis=Workflow.MIP_DNA,
        customer_id="cust001",
    )
    helpers.add_relationship(store=store, sample=related_dna_sample, case=related_dna_case_1)
    StoreHelpers.add_analysis(store=store, case=related_dna_case_1, uploaded_at=datetime.now())

    related_dna_case_2: Case = helpers.add_case(
        store=store,
        internal_id="related_dna_case_2",
        data_analysis=Workflow.BALSAMIC,
        customer_id="cust000",
    )
    helpers.add_relationship(store=store, sample=related_dna_sample, case=related_dna_case_2)

    not_related_dna_case: Case = helpers.add_case(
        store=store,
        internal_id="not_related_dna_case",
        name="not_related_dna_case",
        data_analysis=Workflow.RNAFUSION,
        customer_id="cust000",
    )
    helpers.add_relationship(store=store, sample=related_dna_sample, case=not_related_dna_case)

    return store


@pytest.fixture
def rna_sample(store_with_rna_and_related_dna_sample_and_cases: Store) -> Sample:
    return store_with_rna_and_related_dna_sample_and_cases.get_sample_by_internal_id(
        internal_id="rna_sample"
    )


@pytest.fixture
def rna_case(store_with_rna_and_related_dna_sample_and_cases: Store) -> Case:
    return store_with_rna_and_related_dna_sample_and_cases.get_case_by_internal_id("rna_case")


@pytest.fixture
def related_dna_cases(store_with_rna_and_related_dna_sample_and_cases: Store) -> list[Case]:
    related_dna_case_1: Case = (
        store_with_rna_and_related_dna_sample_and_cases.get_case_by_internal_id(
            internal_id="related_dna_case_1"
        )
    )
    related_dna_case_2: Case = (
        store_with_rna_and_related_dna_sample_and_cases.get_case_by_internal_id(
            internal_id="related_dna_case_2"
        )
    )
    return [related_dna_case_1, related_dna_case_2]


@pytest.fixture
def uploaded_related_dna_cases(related_dna_cases: list[Case]) -> list[Case]:
    related_uploaded_dna_cases: list[Case] = []
    for case in related_dna_cases:
        if case.is_uploaded:
            related_uploaded_dna_cases.append(case)
    return related_uploaded_dna_cases


@pytest.fixture
def rna_dna_collections_service(
    store_with_rna_and_related_dna_sample_and_cases: Store,
) -> RNADNACollectionsService:
    return RNADNACollectionsService(store_with_rna_and_related_dna_sample_and_cases)
