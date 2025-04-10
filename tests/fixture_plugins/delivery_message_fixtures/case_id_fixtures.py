import pytest


@pytest.fixture
def microsalt_mwx_case_id() -> str:
    """Return a microSALT case ID."""
    return "microsalt_case_1"


@pytest.fixture
def microsalt_case_id_2() -> str:
    """Return a microSALT case ID."""
    return "microsalt_case_2"
