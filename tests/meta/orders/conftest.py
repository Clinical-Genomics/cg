import json

import pytest
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.osticket import MockOsTicket

from cg.meta.orders import OrdersAPI, OrderType
from cg.meta.orders.status import StatusHandler
from cg.meta.orders.ticket_handler import TicketHandler
from cg.models.orders.order import OrderIn
from cg.store import Store


@pytest.fixture
def all_orders_to_submit(
    balsamic_order_to_submit,
    external_order_to_submit,
    fastq_order_to_submit,
    metagenome_order_to_submit,
    microbial_order_to_submit,
    mip_order_to_submit,
    mip_rna_order_to_submit,
    rml_order_to_submit,
    sarscov2_order_to_submit,
):
    return {
        OrderType.BALSAMIC: OrderIn.parse_obj(balsamic_order_to_submit),
        OrderType.EXTERNAL: OrderIn.parse_obj(external_order_to_submit),
        OrderType.FASTQ: OrderIn.parse_obj(fastq_order_to_submit),
        OrderType.METAGENOME: OrderIn.parse_obj(metagenome_order_to_submit),
        OrderType.MICROSALT: OrderIn.parse_obj(microbial_order_to_submit),
        OrderType.MIP_DNA: OrderIn.parse_obj(mip_order_to_submit),
        OrderType.MIP_RNA: OrderIn.parse_obj(mip_rna_order_to_submit),
        OrderType.RML: OrderIn.parse_obj(rml_order_to_submit),
        OrderType.SARS_COV_2: OrderIn.parse_obj(sarscov2_order_to_submit),
    }


@pytest.fixture
def rml_status_data(rml_order_to_submit):
    """Parse rml order example."""
    return StatusHandler.pools_to_status(rml_order_to_submit)


@pytest.fixture
def fastq_status_data(fastq_order_to_submit):
    """Parse fastq order example."""
    return StatusHandler.samples_to_status(fastq_order_to_submit)


@pytest.fixture
def mip_status_data(mip_order_to_submit):
    """Parse scout order example."""
    return StatusHandler.cases_to_status(mip_order_to_submit)


@pytest.fixture
def mip_rna_status_data(mip_rna_order_to_submit):
    """Parse rna order example."""
    return StatusHandler.cases_to_status(mip_rna_order_to_submit)


@pytest.fixture
def external_status_data(external_order_to_submit):
    """Parse external order example."""
    return StatusHandler.cases_to_status(external_order_to_submit)


@pytest.fixture
def microbial_status_data(microbial_order_to_submit):
    """Parse microbial order example."""
    return StatusHandler.microbial_samples_to_status(microbial_order_to_submit)


@pytest.fixture
def metagenome_status_data(metagenome_order_to_submit):
    """Parse metagenome order example."""
    return StatusHandler.samples_to_status(metagenome_order_to_submit)


@pytest.fixture
def balsamic_status_data(balsamic_order_to_submit):
    """Parse cancer order example."""
    return StatusHandler.cases_to_status(balsamic_order_to_submit)


@pytest.fixture(scope="function")
def orders_api(base_store, osticket: MockOsTicket, lims_api: MockLimsAPI):
    return OrdersAPI(lims=lims_api, status=base_store, osticket=osticket)


@pytest.fixture(name="ticket_handler")
def fixture_ticket_handler(store: Store, osticket: MockOsTicket) -> TicketHandler:
    return TicketHandler(status_db=store, osticket_api=osticket)
