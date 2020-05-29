"""Fixtures for lims tests"""

import pytest

from cg.apps.lims.api import LimsAPI


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
def lims_api():
    """Returns a Lims api mock"""
    _lims_api = MockLims()
    return _lims_api


@pytest.fixture
def skeleton_orderform_sample():
    """Get the skeleton for a orderform"""
    return {
        "UDF/priority": "",
        "UDF/Sequencing Analysis": "",
        "UDF/customer": "",
        "Sample/Name": "",
    }
