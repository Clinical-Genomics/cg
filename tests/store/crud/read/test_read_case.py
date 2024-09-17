from cg.store.models import Case, Customer, Sample
from cg.store.store import Store


def test_get_dna_cases_from_sample_within_collaborators(
    store_with_rna_and_dna_samples_and_cases: Store,
    related_dna_sample_1: Sample,
    rna_sample_collaborators: set[Customer],
    related_dna_cases: list[Case],
):
    # GIVEN a database with a sample in several dna cases

    # WHEN getting the dna cases from a sample within the given collaborators
    fetched_related_dna_cases: list[Case] = (
        store_with_rna_and_dna_samples_and_cases._get_dna_cases_from_sample_within_collaborators(
            sample_internal_id=related_dna_sample_1.internal_id,
            collaborators=rna_sample_collaborators,
        )
    )

    # THEN the correct set of cases is returned
    assert set(related_dna_cases) == set(fetched_related_dna_cases)
