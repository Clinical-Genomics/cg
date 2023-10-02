import re

from pydantic import AfterValidator
from typing_extensions import Annotated


def is_valid_sample_internal_id(sample_internal_id: str) -> bool:
    """
    Check if a sample internal id has the correct structure:
    starts with three letters followed by at least three digits.
    """
    return bool(re.search(r"^[A-Za-z]{3}\d{3}", sample_internal_id))


def validate_sample_id(sample_id: str) -> str:
    """Validate a sample id."""
    if not is_valid_sample_internal_id(sample_id):
        raise ValueError(f"{sample_id} is not a valid sample id")
    return sample_id


def remove_index_from_sample_id(sample_id_with_index: str) -> str:
    return sample_id_with_index.split("_")[0]


SampleId = Annotated[
    str,
    AfterValidator(remove_index_from_sample_id),
    AfterValidator(validate_sample_id),
]
