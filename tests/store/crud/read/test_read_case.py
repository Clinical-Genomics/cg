from cg.constants import DNA_WORKFLOWS_WITH_SCOUT_UPLOAD
from cg.store.models import Case, Customer, Sample
from cg.store.store import Store


def test_get_related_cases(
    store_with_rna_and_dna_samples_and_cases: Store,
    related_dna_sample_1: Sample,
    rna_sample_collaborators: set[Customer],
    related_dna_cases: list[Case],
):
    # GIVEN a database with a sample in several cases
    # GIVEN a list of workflows
    workflows = DNA_WORKFLOWS_WITH_SCOUT_UPLOAD
    # WHEN getting the cases from the given sample by the given workflows and within the given collaborators
    fetched_related_dna_cases: list[Case] = (
        store_with_rna_and_dna_samples_and_cases.get_related_cases(
            sample_internal_id=related_dna_sample_1.internal_id,
            workflows=workflows,
            collaborators=rna_sample_collaborators,
        )
    )

    # THEN the correct set of cases is returned
    assert set(related_dna_cases) == set(fetched_related_dna_cases)


def test_get_uploaded_related_dna_cases(
    store_with_rna_and_related_dna_sample_and_cases: Store,
    rna_case: Case,
    uploaded_related_dna_cases: list[Case],
    related_dna_cases: list[Case],
):
    # GIVEN a database with an RNA case and several related DNA cases
    # GIVEN that some of the DNA cases are uploaded and others not
    store: Store = store_with_rna_and_related_dna_sample_and_cases

    # WHEN getting the related DNA cases that are uploaded
    fetched_uploaded_related_dna_cases: list[Case] = store.get_uploaded_related_dna_cases(
        rna_case=rna_case
    )

    # THEN the correct set of cases is returned
    assert set(fetched_uploaded_related_dna_cases) == set(uploaded_related_dna_cases)
    assert set(uploaded_related_dna_cases) != set(related_dna_cases)


def test_get_related_dna_cases_from_rna_case(
    store_with_rna_and_related_dna_sample_and_cases: Store,
    rna_case: Case,
    related_dna_cases: list[Case],
):
    # GIVEN a database with an RNA case and several related DNA cases
    store: Store = store_with_rna_and_related_dna_sample_and_cases

    # WHEN getting the related DNA cases to the given RNA case
    fetched_related_dna_cases: set[Case] = store.get_related_dna_cases_from_rna_case(
        rna_case=rna_case
    )

    # THEN the correct set of cases is returned
    assert fetched_related_dna_cases == set(related_dna_cases)


def test_get_related_dna_cases_from_rna_sample(
    store_with_rna_and_related_dna_sample_and_cases: Store,
    rna_sample: Sample,
    related_dna_cases: list[Case],
):
    # GIVEN a database with an RNA sample, a related DNA sample and several DNA cases containing the DNA sample
    store: Store = store_with_rna_and_related_dna_sample_and_cases

    # WHEN getting the related DNA cases to the given RNA sample
    fetched_related_dna_cases: list[Case] = store._get_related_dna_cases_from_rna_sample(
        rna_sample=rna_sample
    )

    # THEN the correct set of cases is returned
    assert set(fetched_related_dna_cases) == set(related_dna_cases)
