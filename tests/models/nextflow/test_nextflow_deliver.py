from typing import Dict, Optional

import pytest
from pydantic.v1 import ValidationError as PydanticValidationError

from cg.models.nf_analysis import FileDeliverable

## TODO: FIX THESE TESTS


def test_instantiate_file_deliverables(
    nextflow_deliverables: Dict[str, str],
):
    """Tests file delivery object."""
    # GIVEN valid deliverables fields

    # WHEN instantiating a deliverables object
    nextflow_deliverables_object: FileDeliverable = FileDeliverable(**nextflow_deliverables)

    # THEN assert that it was successfully created
    assert isinstance(nextflow_deliverables_object, FileDeliverable)


def test_instantiate_nextflow_deliverables_with_empty_entry(
    nextflow_deliverables_with_empty_entry: Dict[str, Optional[str]],
):
    """Tests nextflow delivery object with empty entry."""
    # WHEN instantiating a deliverables object with an empty entry
    # THEN assert that an error is raised
    with pytest.raises(PydanticValidationError):
        FileDeliverable(**nextflow_deliverables_with_empty_entry)


def test_instantiate_nextflow_deliverables_with_faulty_entry(
    nextflow_deliverables_with_faulty_entry: Dict[str, str],
):
    """
    Tests nextflow delivery object with a not allowed attribute
    """
    # WHEN instantiating a deliverables object with an empty entry
    # THEN assert that an error is raised
    with pytest.raises(PydanticValidationError):
        FileDeliverable(**nextflow_deliverables_with_faulty_entry)


# >           raise validation_error
# E           pydantic.v1.error_wrappers.ValidationError: 2 validation errors for FileDeliverable
# E           format
# E             field required (type=value_error.missing)
# E           path_index
# E             file or directory at path "~" does not exist (type=value_error.path.not_exists; path=~)
