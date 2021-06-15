import pytest


@pytest.fixture(name="ticket_id")
def fixture_ticked_id() -> int:
    """Return fixture for ticket id used in rsync tests"""
    return 999999


@pytest.fixture(name="internal_id")
def fixture_internal_id() -> str:
    """Return fixture for internal id used in rsync tests"""
    return "angrybird"
