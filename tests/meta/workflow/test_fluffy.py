import pytest

from typing import Dict, List

from cg.meta.workflow.fluffy import (
    get_data_header_key,
    validate_sample_sheet_column_names,
    get_column_names,
)


@pytest.mark.parametrize(
    "sample_sheet_structure", ["bcl_convert_sample_sheet", "bcl_2_fastq_sample_sheet"]
)
def test_data_header_key(
    sample_sheet_structure: str, sample_sheet_structures: Dict[str, Dict[str, List[str]]]
):
    """Test that the correct data header key is returned."""
    assert get_data_header_key(sample_sheet_structures[sample_sheet_structure])


def test_get_data_header_with_incorrect_sample_sheet_structure(sample_sheet_structures):
    """Test that the correct data header key is returned with incorrect sample sheet structure."""
    with pytest.raises(ValueError):
        get_data_header_key(sample_sheet_structures["incorrect_sample_sheet_structure"])


@pytest.mark.parametrize(
    "sample_sheet_structure", ["bcl_convert_sample_sheet", "bcl_2_fastq_sample_sheet"]
)
def test_validate_sample_sheet_column_names(
    sample_sheet_structure: str, sample_sheet_structures: Dict[str, Dict[str, List[str]]]
):
    """Test that the sample sheet column names are valid."""

    # GIVEN a correct sample sheet structure
    sample_sheet_structure = sample_sheet_structures[sample_sheet_structure]

    # GIVEN a sample sheet structure with a correct data header key
    data_header_key: str = get_data_header_key(sample_sheet_structure)

    # GIVEN a sample sheet structure with correct column names
    column_names: List[str] = get_column_names(
        sample_sheet_structure, data_header_key=data_header_key
    )

    # WHEN we validate the column names
    try:
        validate_sample_sheet_column_names(column_names)
    except ValueError:
        pytest.fail("validate_sample_sheet_column_names() raised an unexpected ValueError!")

    # THEN no errors should be raised
