import pytest

from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.meta.orders import OrdersAPI
from cg.meta.orders.ticket_handler import TicketHandler
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.orders.store_order_services.storing_service_registry import (
    StoringServiceRegistry,
    setup_order_submitter_registry,
)
from cg.store.store import Store
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture
def freshdesk_client():
    return FreshdeskClient(base_url="https://mock.freshdesk.com", api_key="mock_api_key")


@pytest.fixture
def order_validation_service(base_store: Store) -> OrderValidationService:
    return OrderValidationService(base_store)


@pytest.fixture(scope="function")
def orders_api(
    base_store: Store,
    ticket_handler: TicketHandler,
    lims_api: MockLimsAPI,
    order_submitter_registry: StoringServiceRegistry,
    order_validation_service: OrderValidationService,
) -> OrdersAPI:
    return OrdersAPI(
        lims=lims_api,
        ticket_handler=ticket_handler,
        submitter_registry=order_submitter_registry,
        validation_service=order_validation_service,
    )


@pytest.fixture
def ticket_handler(store: Store, freshdesk_client: FreshdeskClient) -> TicketHandler:
    return TicketHandler(db=store, client=freshdesk_client, system_email_id=12345, env="production")


@pytest.fixture
def order_submitter_registry(base_store: Store, lims_api: MockLimsAPI) -> StoringServiceRegistry:
    return setup_order_submitter_registry(lims=lims_api, status_db=base_store)
