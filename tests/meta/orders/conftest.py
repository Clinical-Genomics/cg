from pathlib import Path

import pytest

from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.meta.orders import OrdersAPI
from cg.meta.orders.ticket_handler import TicketHandler
from cg.services.orders.submitters.order_submitter_registry import (
    OrderSubmitterRegistry,
    setup_order_submitter_registry,
)
from cg.store.store import Store
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture
def freshdesk_client():
    return FreshdeskClient(base_url="https://example.com", api_key="dummy_api_key")


@pytest.fixture(scope="function")
def orders_api(
    base_store,
    osticket: MockOsTicket,
    lims_api: MockLimsAPI,
    order_submitter_registry: OrderSubmitterRegistry,
) -> OrdersAPI:
    return OrdersAPI(
        lims=lims_api,
        status=base_store,
        osticket=osticket,
        submitter_registry=order_submitter_registry,
    )
def orders_api(base_store: Store, lims_api: MockLimsAPI, ticket_handler: TicketHandler):
    return OrdersAPI(lims=lims_api, status=base_store, ticket_handler=ticket_handler)


@pytest.fixture
def ticket_handler(store: Store, osticket: MockOsTicket) -> TicketHandler:
    return TicketHandler(status_db=store, osticket_api=osticket)


@pytest.fixture
def order_submitter_registry(base_store: Store, lims_api: MockLimsAPI) -> OrderSubmitterRegistry:
    return setup_order_submitter_registry(lims=lims_api, status_db=base_store)
def ticket_handler(store: Store, freshdesk_client: FreshdeskClient):
    return TicketHandler(status_db=store, client=freshdesk_client, system_email_id=1, env="test")
