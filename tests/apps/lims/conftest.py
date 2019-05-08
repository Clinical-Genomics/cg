import pytest
from cg.apps.lims.api import LimsAPI


@pytest.fixture
def balsamic_orderform():
    """Orderform fixture for Balsamic samples"""
    return 'tests/fixtures/orderforms/1508.17.balsamic.xlsx'


@pytest.fixture
def external_orderform():
    """Orderform fixture for external samples"""
    return 'tests/fixtures/orderforms/1541.6.external.xlsx'


@pytest.fixture
def fastq_orderform():
    """Orderform fixture for fastq samples"""
    return 'tests/fixtures/orderforms/1508.17.fastq.xlsx'


@pytest.fixture
def metagenome_orderform():
    """Orderform fixture for metagenome samples"""
    return 'tests/fixtures/orderforms/1605.6.metagenome.xlsx'


@pytest.fixture
def microbial_orderform():
    """Orderform fixture for microbial samples"""
    return 'tests/fixtures/orderforms/1603.7.microbial.xlsx'


@pytest.fixture
def mip_orderform():
    """Orderform fixture for MIP samples"""
    return 'tests/fixtures/orderforms/1508.17.mip.xlsx'


@pytest.fixture
def mip_balsamic_orderform():
    """Orderform fixture for MIP and Balsamic samples"""
    return 'tests/fixtures/orderforms/1508.17.mip_balsamic.xlsx'


@pytest.fixture
def rml_orderform():
    """Orderform fixture for RML samples"""
    return 'tests/fixtures/orderforms/1604.9.rml.xlsx'


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
