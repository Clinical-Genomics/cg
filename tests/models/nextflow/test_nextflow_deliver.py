from pathlib import Path

import pytest
from pydantic.v1 import ValidationError as PydanticValidationError

from cg.models.nf_analysis import FileDeliverable


def test_file_deliverables(deliverable_id: str, file_format: str, step: str, existing_file: Path):
    """Tests file delivery."""
    # GIVEN valid deliverables fields

    # WHEN instantiating a deliverables object
    file_deliverable: FileDeliverable = FileDeliverable(
        format=file_format,
        id=deliverable_id,
        path=existing_file,
        path_index=existing_file,
        step=step,
        tag=step,
    )

    # THEN assert that it was successfully created
    assert isinstance(file_deliverable, FileDeliverable)


def test_file_deliverables_missing_optional(
    deliverable_id: str, file_format: str, step: str, existing_file: Path
):
    """Tests file delivery when an optional field is missing."""
    # GIVEN valid deliverables fields

    # WHEN instantiating a deliverables object
    file_deliverable: FileDeliverable = FileDeliverable(
        format=file_format,
        id=deliverable_id,
        path=existing_file,
        step=step,
        tag=step,
    )

    # THEN assert that it was successfully created
    assert isinstance(file_deliverable, FileDeliverable)


def test_file_deliverables_missing_mandatory(
    deliverable_id: str,
    step: str,
    existing_file: Path,
):
    """Tests file delivery when a mandatory field is missing."""
    # GIVEN valid deliverables fields

    # WHEN instantiating a deliverables object
    # THEN assert that an error is raised
    with pytest.raises(PydanticValidationError) as error:
        FileDeliverable(
            id=deliverable_id,
            path=existing_file,
            step=step,
            tag=step,
        )
    # THEN assert the error message
    assert "field required (type=value_error.missing)" in str(error.value)


def test_file_deliverables_non_existing_attribute(
    deliverable_id: str, file_format: str, step: str, existing_file: Path
):
    """Tests file delivery when a non existing attribute is given."""
    # GIVEN valid deliverables fields

    # WHEN instantiating a deliverables object
    file_deliverable: FileDeliverable = FileDeliverable(
        format=file_format,
        id=deliverable_id,
        path=existing_file,
        step=step,
        tag=step,
        nonexisting=file_format,
    )

    # THEN assert that it was successfully created
    assert isinstance(file_deliverable, FileDeliverable)

    # THEN assert that not existing attribute is not included
    assert "nonexisting" not in file_deliverable.__annotations__.keys()


def test_file_deliverables_non_existing_file(
    deliverable_id: str,
    file_format: str,
    step: str,
    non_existing_file: Path,
):
    """Tests file delivery when a mandatory file does not exist."""
    # GIVEN valid deliverables fields

    # WHEN instantiating a deliverables object
    # THEN assert that an error is raised
    with pytest.raises(PydanticValidationError) as error:
        FileDeliverable(
            format=file_format,
            id=deliverable_id,
            path=non_existing_file,
            step=step,
            tag=step,
        )
    # THEN assert the error message
    assert "value_error.path.not_exists" in str(error.value)
