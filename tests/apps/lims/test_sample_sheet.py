"""Tests for lims functions that are related with sample sheets."""
from typing import Match

from cg.apps.lims.sample_sheet import extract_sequence_in_parentheses


def test_extract_sequence_in_parentheses(reagent_label: str, reagent_sequence: str):
    """Test that the correct index is fetched from the reagent label."""
    # GIVEN a reagent with compatible label and sequence

    # WHEN getting the index
    match: Match = extract_sequence_in_parentheses(label=reagent_label)

    # THEN the index is what is expected
    assert match.group(1) == reagent_sequence
