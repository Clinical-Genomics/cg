import pytest
from cg.apps.lims.api import LimsAPI


class MockLims(LimsAPI):

    lims = None

    def __init__(self):
        self.lims = self
        pass

    _received_at = None
    _delivered_at = None

    def get_prepmethod(self, lims_id: str) -> str:
        pass

    def get_sequencingmethod(self, lims_id: str) -> str:
        pass

    def get_deliverymethod(self, lims_id: str) -> str:
        pass

    def set_received_date(self, date):
        self._received_at = date

    def get_received_date(self, lims_id: str):
        return self._received_at

    def set_delivery_date(self, date):
        self._delivered_at = date

    def get_delivery_date(self, lims_id: str):
        return self._delivered_at


@pytest.fixture(scope='function')
def lims_api():

    _lims_api = MockLims()
    return _lims_api


@pytest.fixture
def skeleton_orderform_sample():
    return {
        'UDF/priority': '',
        'UDF/Sequencing Analysis': '',
        'UDF/customer': '',
        'Sample/Name': '',
        }
