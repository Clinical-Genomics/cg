"""Tests for lims functions that are related with sample sheets."""

from cg.apps.lims.sample_sheet import extract_sequence_in_parentheses


def test_extract_sequence_in_parentheses(reagent_label: str, reagent_sequence: str):
    """Test that the correct index is fetched from the reagent label."""
    # GIVEN a reagent with compatible label and sequence

    # WHEN getting the index
    extracted_sequence: str = extract_sequence_in_parentheses(label=reagent_label)

    # THEN the index is what is expected
    assert extracted_sequence == reagent_sequence


def test_extract_sequence_in_parentheses_invalid_reagent(
    invalid_reagent_label: str, invalid_reagent_sequence: str
):
    """Test that the extracted index is not the same as the reagent sequence."""
    # GIVEN a reagent with compatible label and sequence

    # WHEN getting the index
    extracted_sequence: str = extract_sequence_in_parentheses(label=invalid_reagent_label)

    # THEN the index is what is expected
    assert extracted_sequence != invalid_reagent_sequence


def test_extract_sequence_in_parentheses_no_parentheses(label_no_parentheses: str):
    """Test using a label without parentheses returns None."""
    # GIVEN a reagent with compatible label and sequence

    # WHEN getting the index
    extracted_sequence: str = extract_sequence_in_parentheses(label=label_no_parentheses)

    # THEN the index is what is expected
    assert extracted_sequence is None
