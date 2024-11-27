from cg.store.models import Case
from cg.store.store import Store


def test_get_uploaded_related_dna_case(
    store_with_rna_and_dna_samples_and_cases: Store,
    rna_case: Case,
    uploaded_related_dna_case: list[Case],
    related_dna_cases: list[Case],
):
    # GIVEN a database with an RNA case and several related DNA cases
    # GIVEN that some of the DNA cases are uploaded and others not
    store: Store = store_with_rna_and_dna_samples_and_cases

    # WHEN getting the related DNA cases that are uploaded
    fetched_uploaded_related_dna_case: list[Case] = store.get_uploaded_related_dna_cases(
        rna_case=rna_case,
    )

    # THEN the correct set of cases is returned
    assert set(fetched_uploaded_related_dna_case) == set(uploaded_related_dna_case)
    assert set(fetched_uploaded_related_dna_case) != set(related_dna_cases)
