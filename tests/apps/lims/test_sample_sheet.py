"""Tests for lims functions that are related with sample sheets."""
from cg.apps.lims.sample_sheet import get_index

from tests.mocks.limsmock import MockLimsAPI


def test_get_index_with_label(lims_api: MockLimsAPI, reagent_label: str):
    """Test that the correct index is fetched from the reagent label.."""
    # GIVEN a lims api with a reagent and a valid reagent label
    sequence: str = lims_api.get_reagent_types().pop().sequence

    # WHEN getting the index
    index: str = get_index(lims=lims_api, label=reagent_label)

    # THEN the index is what is expected
    assert index == sequence
