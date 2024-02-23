"""Fixtures for lims tests"""

import pytest

from cg.apps.lims.api import LimsAPI
from tests.mocks.limsmock import MockReagentType


class MockLims(LimsAPI):
    """Mock parts of the lims api"""

    lims = None

    def __init__(self):
        """Mock the init method"""
        self.lims = self

    def get_prepmethod(self, lims_id: str) -> str:
        """Override the get_prepmethod"""

    def get_sequencingmethod(self, lims_id: str) -> str:
        """Override the get_sequencingmethod"""

    def get_deliverymethod(self, lims_id: str) -> str:
        """Override the get_deliverymethod"""


@pytest.fixture(scope="function")
def lims_mock():
    """Returns a Lims api mock"""
    _lims_api = MockLims()
    return _lims_api


@pytest.fixture
def reagent() -> MockReagentType:
    """Return a valid MockReagentType."""
    return MockReagentType(label="A702-A506 (ACAGTGGT-CTAGAACA)", sequence="ACAGTGGT-CTAGAACA")


@pytest.fixture
def reagent_label(reagent: MockReagentType) -> str:
    """Returns a reagent label."""
    return reagent.label


@pytest.fixture
def reagent_sequence(reagent: MockReagentType) -> str:
    """Returns a reagent sequence."""
    return reagent.sequence


@pytest.fixture
def invalid_reagent() -> MockReagentType:
    """Return a MockReagentType with invalid data."""
    return MockReagentType(label="A702-A506 (ACAGTGGT-CTAGAACA)", sequence="CTAGAACA-ACAGTGGT")


@pytest.fixture
def invalid_reagent_label(invalid_reagent: MockReagentType) -> str:
    """Returns a reagent label."""
    return invalid_reagent.label


@pytest.fixture
def invalid_reagent_sequence(invalid_reagent: MockReagentType) -> str:
    """Returns a reagent sequence."""
    return invalid_reagent.sequence


@pytest.fixture
def label_no_parentheses() -> str:
    """Returns a reagent label."""
    return "ACAGTGGT-CTAGAACA"
