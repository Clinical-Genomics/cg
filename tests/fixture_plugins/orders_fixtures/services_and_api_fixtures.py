import pytest

from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.services.orders.storing.service_registry import (
    StoringServiceRegistry,
    setup_storing_service_registry,
)
from cg.services.orders.submitter.service import OrderSubmitter
from cg.services.orders.submitter.ticket_handler import TicketHandler
from cg.services.orders.validation.service import OrderValidationService
from cg.store.store import Store
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture
def freshdesk_client() -> FreshdeskClient:
    return FreshdeskClient(base_url="https://mock.freshdesk.com", api_key="mock_api_key")


@pytest.fixture
def order_validation_service(store_with_all_test_applications: Store) -> OrderValidationService:
    return OrderValidationService(store_with_all_test_applications)


@pytest.fixture(scope="function")
def order_submitter(
    ticket_handler: TicketHandler,
    lims_api: MockLimsAPI,
    storing_service_registry: StoringServiceRegistry,
    order_validation_service: OrderValidationService,
) -> OrderSubmitter:
    return OrderSubmitter(
        lims=lims_api,
        ticket_handler=ticket_handler,
        storing_registry=storing_service_registry,
        validation_service=order_validation_service,
    )


@pytest.fixture
def ticket_handler(store: Store, freshdesk_client: FreshdeskClient) -> TicketHandler:
    return TicketHandler(db=store, client=freshdesk_client, system_email_id=12345, env="production")


@pytest.fixture
def storing_service_registry(
    store_with_all_test_applications: Store, lims_api: MockLimsAPI
) -> StoringServiceRegistry:
    return setup_storing_service_registry(lims=lims_api, status_db=store_with_all_test_applications)
