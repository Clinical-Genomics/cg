"""Tests for lims functions that are related with sample sheets."""
from typing import Match

from cg.apps.lims.sample_sheet import extract_sequence_in_parentheses
from tests.mocks.limsmock import MockLimsAPI


def test_extract_sequence_in_parentheses(lims_api: MockLimsAPI, reagent_label: str):
    """Test that the correct index is fetched from the reagent label."""
    # GIVEN a lims api with a reagent and a valid reagent label
    sequence: str = lims_api.get_reagent_types().pop().sequence

    # WHEN getting the index
    match: Match = extract_sequence_in_parentheses(label=reagent_label)

    # THEN the index is what is expected
    assert match.group(1) == sequence
