from pathlib import Path

import pytest
from pydantic.v1 import ValidationError as PydanticValidationError

from cg.constants.constants import FileFormat
from cg.exc import ValidationError
from cg.models.nf_analysis import FileDeliverable


def test_file_deliverables(any_string: str, filled_file: Path):
    """Tests that file deliverable model is successfully created."""
    # GIVEN valid deliverables fields

    # WHEN instantiating a deliverables object
    file_deliverable = FileDeliverable(
        format=FileFormat.TSV,
        id=any_string,
        path=filled_file,
        path_index=filled_file,
        step=any_string,
        tag=any_string,
    )

    # THEN assert that it was successfully created
    assert isinstance(file_deliverable, FileDeliverable)

    # THEN assert that paths are returned as strings
    assert isinstance(file_deliverable.path, str)
    assert isinstance(file_deliverable.path_index, str)


def test_file_deliverables_missing_optional(any_string: str, filled_file: Path):
    """Tests file delivery when an optional field is missing."""
    # GIVEN valid deliverables fields

    # WHEN instantiating a deliverables object
    file_deliverable = FileDeliverable(
        format=FileFormat.TSV,
        id=any_string,
        path=filled_file,
        step=any_string,
        tag=any_string,
    )

    # THEN assert that it was successfully created
    assert isinstance(file_deliverable, FileDeliverable)


def test_file_deliverables_missing_mandatory(
    any_string: str,
    filled_file: Path,
):
    """Tests file delivery when a mandatory field is missing."""
    # WHEN instantiating a deliverables object with a missing field

    # THEN assert that an error is raised
    with pytest.raises(PydanticValidationError) as error:
        FileDeliverable(
            id=any_string,
            path=filled_file,
            step=any_string,
            tag=any_string,
        )
    # THEN assert the error message
    assert "field required (type=value_error.missing)" in str(error.value)


def test_file_deliverables_non_existing_attribute(any_string: str, filled_file: Path):
    """Tests file delivery when a non existing attribute is given."""
    # WHEN instantiating a deliverables object with additional attributes not present in the model
    file_deliverable = FileDeliverable(
        format=FileFormat.TSV,
        id=any_string,
        path=filled_file,
        step=any_string,
        tag=any_string,
        nonexisting=FileFormat.TSV,
    )

    # THEN assert that it was successfully created
    assert isinstance(file_deliverable, FileDeliverable)

    # THEN assert that not existing attribute is not included
    assert "nonexisting" not in file_deliverable.__annotations__.keys()


def test_file_deliverables_non_existing_file(
    any_string: str,
    non_existing_file_path: Path,
):
    """Tests file delivery when a mandatory file does not exist."""
    # WHEN instantiating a deliverables object

    # THEN assert that an error is raised
    file_deliverable = FileDeliverable(
        format=FileFormat.TSV,
        id=any_string,
        path=non_existing_file_path,
        step=any_string,
        tag=any_string,
    )
    # THEN assert that it was successfully created
    assert isinstance(file_deliverable, FileDeliverable)
