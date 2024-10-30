from cg.services.store.rna_dna_collections_service.rna_dna_collections_service import (
    RNADNACollectionsService,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_get_uploaded_related_dna_cases(
    rna_case: Case,
    rna_dna_collections_service: RNADNACollectionsService,
    uploaded_related_dna_cases: list[Case],
    related_dna_cases: list[Case],
):
    # GIVEN a database with an RNA case and several related DNA cases
    # GIVEN that some of the DNA cases are uploaded and others not
    # GIVEN an RNADNACollectionsService

    # WHEN getting the related DNA cases that are uploaded
    fetched_uploaded_related_dna_cases: list[Case] = (
        rna_dna_collections_service.get_uploaded_related_dna_cases(rna_case=rna_case)
    )

    # THEN the correct set of cases is returned
    assert set(fetched_uploaded_related_dna_cases) == set(uploaded_related_dna_cases)
    assert set(uploaded_related_dna_cases) != set(related_dna_cases)


def test_get_related_dna_cases_from_rna_case(
    store_with_rna_and_related_dna_sample_and_cases: Store,
    rna_case: Case,
    rna_dna_collections_service: RNADNACollectionsService,
    related_dna_cases: list[Case],
):
    # GIVEN a database with an RNA case and several related DNA cases
    # GIVEN an RNADNACollectionsService

    # WHEN getting the related DNA cases to the given RNA case
    fetched_related_dna_cases: set[Case] = (
        rna_dna_collections_service.get_related_dna_cases_from_rna_case(rna_case=rna_case)
    )

    # THEN the correct set of cases is returned
    assert fetched_related_dna_cases == set(related_dna_cases)


def test_get_related_dna_cases_from_rna_sample(
    store_with_rna_and_related_dna_sample_and_cases: Store,
    rna_sample: Sample,
    rna_dna_collections_service: RNADNACollectionsService,
    related_dna_cases: list[Case],
):
    # GIVEN a database with an RNA sample, a related DNA sample and several DNA cases containing the DNA sample
    # GIVEN an RNADNACollectionsService

    # WHEN getting the related DNA cases to the given RNA sample
    fetched_related_dna_cases: list[Case] = (
        rna_dna_collections_service._get_related_dna_cases_from_rna_sample(rna_sample=rna_sample)
    )

    # THEN the correct set of cases is returned
    assert set(fetched_related_dna_cases) == set(related_dna_cases)
