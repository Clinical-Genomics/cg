from cg.constants import Workflow
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

    workflows = [
        Workflow.MIP_DNA,
        Workflow.BALSAMIC,
        Workflow.BALSAMIC_UMI,
    ]

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
