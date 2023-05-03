from pathlib import Path

import pytest

from cg.constants import FileExtensions
from cg.exc import ValidationError
from cg.io.validate_path import validate_file_suffix


def test_validate_file_suffix_correct_suffix(csv_file_path: Path):
    """Test validate file suffix when file suffix is in correct format."""
    # GIVEN a existing file in the correct file format
    assert csv_file_path.exists()

    # WHEN validating the file suffix
    was_validated: bool = validate_file_suffix(
        path_to_validate=csv_file_path, target_suffix=FileExtensions.CSV
    )

    # THEN assert the suffix is in the correct format
    assert was_validated


def test_validate_file_suffix_wrong_suffix(caplog, json_file_path: Path):
    """Test validate file suffix when file suffix is in wrong format."""
    # GIVEN a existing file in the wrong file format
    assert json_file_path.exists()
    assert json_file_path.suffix != FileExtensions.CSV

    # WHEN validating the file suffix
    with pytest.raises(ValidationError):
        validate_file_suffix(path_to_validate=json_file_path, target_suffix=FileExtensions.CSV)

        # THEN assert the suffix is in the wrong format
        assert "seems to be in wrong format" in caplog.text
