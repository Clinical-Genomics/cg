import pytest
from cg.store.models import Case
from cg.store.store import Store


@pytest.mark.parametrize(
    "store_with_cases",
    [
        "store_with_rna_and_dna_samples_and_cases",
        "store_with_multiple_rna_and_dna_samples_and_cases",
    ],
    ids=["single_rna_sample", "multiple_rna_samples"],
)
def test_get_uploaded_related_dna_case(
    store_with_cases: str,
    rna_case: Case,
    uploaded_related_dna_case: list[Case],
    related_dna_cases: list[Case],
    request: pytest.FixtureRequest,
):
    # GIVEN a database with an RNA case and several related DNA cases
    # GIVEN that some of the DNA cases are uploaded and others not
    store: Store = request.getfixturevalue(store_with_cases)

    # WHEN getting the related DNA cases that are uploaded
    fetched_uploaded_related_dna_case: list[Case] = store.get_uploaded_related_dna_cases(
        rna_case=rna_case,
    )

    # THEN the correct set of cases is returned
    assert fetched_uploaded_related_dna_case == uploaded_related_dna_case
    assert fetched_uploaded_related_dna_case != related_dna_cases
