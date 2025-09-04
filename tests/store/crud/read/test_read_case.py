import pytest

from cg.exc import CaseNotFoundError
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


def test_get_case_by_internal_id_strict_works(store_with_cases_and_customers: Store):
    """Test that get_case_by_internal_id_strict returns the correct case."""
    # GIVEN a store with a case
    internal_id: str = store_with_cases_and_customers.get_cases()[0].internal_id

    # WHEN fetching the case by internal id
    case: Case = store_with_cases_and_customers.get_case_by_internal_id_strict(internal_id)

    # THEN it returns a case
    assert isinstance(case, Case)
    # THEN no errors should be raised


def test_get_case_by_internal_id_strict_fails(store_with_cases_and_customers: Store):
    """Test that looking for a case with a non-existent internal id raises an error."""

    # GIVEN a fake internal id
    internal_id: str = "fake"

    # WHEN fetching a case using the fake internal id

    # THEN the method should raise a CaseNotFoundError
    with pytest.raises(CaseNotFoundError) as error:
        store_with_cases_and_customers.get_case_by_internal_id_strict(internal_id)

    # THEN the error message should be as expected
    assert str(error.value) == f"Case with internal id {internal_id} was not found in the database."
