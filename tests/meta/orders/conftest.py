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
    config = {
        "freshdesk_url": "https://example.com",
        "freshdesk_api_key": "dummy_api_key"
    }
    return FreshdeskClient(config=config)


@pytest.fixture(scope="function")
def orders_api(
    base_store: Store,
    ticket_handler: TicketHandler,
    lims_api: MockLimsAPI,
    order_submitter_registry: OrderSubmitterRegistry,
) -> OrdersAPI:
    return OrdersAPI(
        lims=lims_api,
        status=base_store,
        ticket_handler=ticket_handler,
        submitter_registry=order_submitter_registry,
    )


@pytest.fixture
def ticket_handler(store: Store, freshdesk_client: FreshdeskClient) -> TicketHandler:
    config = {
        "freshdesk_order_email_id": 12345,
        "freshdesk_environment": "production"
    }
    return TicketHandler(config=config, db=store, client=freshdesk_client)



@pytest.fixture
def order_submitter_registry(base_store: Store, lims_api: MockLimsAPI) -> OrderSubmitterRegistry:
    return setup_order_submitter_registry(lims=lims_api, status_db=base_store)
