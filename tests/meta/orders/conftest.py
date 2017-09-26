import json

import pytest

from cg.apps.osticket import OsTicket
from cg.meta.orders import OrdersAPI, OrderType
from cg.meta.orders.status import StatusHandler


@pytest.fixture
def scout_order():
    """Load an example scout order."""
    json_path = 'tests/fixtures/orders/scout.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def external_order():
    """Load an example external order."""
    json_path = 'tests/fixtures/orders/external.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def fastq_order():
    """Load an example fastq order."""
    json_path = 'tests/fixtures/orders/fastq.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def rml_order():
    """Load an example rml order."""
    json_path = 'tests/fixtures/orders/rml.json'
    json_data = json.load(open(json_path))
    return json_data


@pytest.fixture
def all_orders(rml_order, fastq_order, scout_order, external_order):
    return {
        OrderType.RML: rml_order,
        OrderType.FASTQ: fastq_order,
        OrderType.SCOUT: scout_order,
        OrderType.EXTERNAL: external_order,
    }


@pytest.fixture
def rml_status_data(rml_order):
    """Parse rml order example."""
    data = StatusHandler.pools_to_status(rml_order)
    return data


@pytest.fixture
def fastq_status_data(fastq_order):
    """Parse fastq order example."""
    data = StatusHandler.samples_to_status(fastq_order)
    return data


@pytest.fixture
def scout_status_data(scout_order):
    """Parse scout order example."""
    data = StatusHandler.families_to_status(scout_order)
    return data


@pytest.fixture(scope='function')
def orders_api(base_store):
    osticket_api = OsTicket()
    _orders_api = OrdersAPI(lims=None, status=base_store, osticket=osticket_api)
    return _orders_api
