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


@pytest.fixture(name="lims_mock", scope="function")
def lims_api():
    """Returns a Lims api mock"""
    _lims_api = MockLims()
    return _lims_api


@pytest.fixture(name="reagent_label")
def fixture_reagent_label() -> str:
    """Returns a reagent label."""
    return MockReagentType().label
