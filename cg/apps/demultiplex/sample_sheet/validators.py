import re


def is_valid_sample_internal_id(sample_internal_id: str) -> bool:
    """
    Check if a sample internal id has the correct structure:
    starts with three letters followed by at least three digits.
    """
    return bool(re.search(r"^[A-Za-z]{3}\d{3}", sample_internal_id))
