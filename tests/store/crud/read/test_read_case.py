from cg.store.models import Case
from cg.store.store import Store


def test_get_uploaded_related_dna_case(
    store_with_rna_and_related_dna_sample_and_cases: Store,
    rna_case: Case,
    uploaded_related_dna_case_ids: list[str],
    related_dna_case_ids: list[str],
):
    # GIVEN a database with an RNA case and several related DNA cases
    # GIVEN that some of the DNA cases are uploaded and others not
    store: Store = store_with_rna_and_related_dna_sample_and_cases

    # WHEN getting the related DNA cases that are uploaded
    fetched_uploaded_related_dna_case_ids: list[str] = store.get_uploaded_related_dna_case_ids(
        rna_case_id=rna_case.internal_id,
    )

    # THEN the correct set of cases is returned
    assert set(fetched_uploaded_related_dna_case_ids) == set(uploaded_related_dna_case_ids)
    assert set(fetched_uploaded_related_dna_case_ids) != set(related_dna_case_ids)
