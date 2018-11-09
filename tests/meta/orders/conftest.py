import json

import pytest
from cg.apps.lims import LimsAPI

from cg.apps.osticket import OsTicket
from cg.meta.orders import OrdersAPI, OrderType
from cg.meta.orders.status import StatusHandler


class MockLims(LimsAPI):

    lims = None

    def __init__(self):
        self.lims = self

    def update_sample(self, lims_id: str, sex=None, application: str=None,
                      target_reads: int=None):
        pass


@pytest.fixture
def scout_order_to_submit():
    """Load an example scout order."""
    json_path = 'tests/fixtures/orders/scout.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def external_order_to_submit():
    """Load an example external order."""
    json_path = 'tests/fixtures/orders/external.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def fastq_order_to_submit():
    """Load an example fastq order."""
    json_path = 'tests/fixtures/orders/fastq.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def rml_order_to_submit():
    """Load an example rml order."""
    json_path = 'tests/fixtures/orders/rml.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def metagenome_order_to_submit():
    """Load an example metagenome order."""
    json_path = 'tests/fixtures/orders/metagenome.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def microbial_order_to_submit():
    """Load an example microbial order."""
    json_path = 'tests/fixtures/orders/microbial.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def cancer_order_to_submit():
    """Load an example cancer order."""
    json_path = 'tests/fixtures/orders/cancer.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def all_orders_to_submit(rml_order_to_submit, fastq_order_to_submit, scout_order_to_submit,
                         external_order_to_submit, microbial_order_to_submit,
                         metagenome_order_to_submit, cancer_order_to_submit):
    return {
        OrderType.RML: rml_order_to_submit,
        OrderType.FASTQ: fastq_order_to_submit,
        OrderType.SCOUT: scout_order_to_submit,
        OrderType.EXTERNAL: external_order_to_submit,
        OrderType.MICROBIAL: microbial_order_to_submit,
        OrderType.METAGENOME: metagenome_order_to_submit,
        OrderType.CANCER: cancer_order_to_submit,
    }


@pytest.fixture
def rml_status_data(rml_order_to_submit):
    """Parse rml order example."""
    data = StatusHandler.pools_to_status(rml_order_to_submit)
    return data


@pytest.fixture
def fastq_status_data(fastq_order_to_submit):
    """Parse fastq order example."""
    data = StatusHandler.samples_to_status(fastq_order_to_submit)
    return data


@pytest.fixture
def scout_status_data(scout_order_to_submit):
    """Parse scout order example."""
    data = StatusHandler.families_to_status(scout_order_to_submit)
    return data


@pytest.fixture
def external_status_data(external_order_to_submit):
    """Parse external order example."""
    data = StatusHandler.families_to_status(external_order_to_submit)
    return data


@pytest.fixture
def microbial_status_data(microbial_order_to_submit):
    """Parse microbial order example."""
    data = StatusHandler.microbial_samples_to_status(microbial_order_to_submit)
    return data


@pytest.fixture
def metagenome_status_data(metagenome_order_to_submit):
    """Parse metagenome order example."""
    data = StatusHandler.samples_to_status(metagenome_order_to_submit)
    return data


@pytest.fixture
def cancer_status_data(cancer_order_to_submit):
    """Parse cancer order example."""
    data = StatusHandler.samples_to_status(cancer_order_to_submit)
    return data


@pytest.fixture(scope='function')
def orders_api(base_store):
    osticket_api = OsTicket()
    lims = MockLims()
    _orders_api = OrdersAPI(lims=lims, status=base_store, osticket=osticket_api)
    return _orders_api
