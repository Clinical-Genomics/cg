import pytest
from cg.apps.lims.api import LimsAPI

@pytest.fixture
def rml_orderform():
    return 'tests/fixtures/orderforms/1604.8.rml.xlsx'


@pytest.fixture
def fastq_orderform():
    return 'tests/fixtures/orderforms/1508.14.fastq.xlsx'


@pytest.fixture
def scout_orderform():
    return 'tests/fixtures/orderforms/1508.14.mip.xlsx'


@pytest.fixture
def external_orderform():
    return 'tests/fixtures/orderforms/1541.6.external.xlsx'


@pytest.fixture
def microbial_orderform():
    return 'tests/fixtures/orderforms/1603.6.microbial.xlsx'


@pytest.fixture
def metagenome_orderform():
    return 'tests/fixtures/orderforms/1605.4.metagenome.xlsx'


@pytest.fixture
def cancer_orderform():
    return 'tests/fixtures/orderforms/1508.14.balsamic.xlsx'


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
def microbial_orderform():
    return 'tests/fixtures/orderforms/1603.6.microbial.xlsx'


@pytest.fixture
def skeleton_orderform_sample():
    return {
        'UDF/priority': '',
        'UDF/Sequencing Analysis': '',
        'UDF/customer': '',
        'Sample/Name': '',
        }
