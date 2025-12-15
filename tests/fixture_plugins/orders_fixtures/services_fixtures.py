from unittest.mock import create_autospec

import pytest

from cg.apps.lims.api import LimsAPI
from cg.clients.freshdesk.freshdesk_client import FreshdeskClient
from cg.services.orders.storing.service_registry import (
    StoringServiceRegistry,
    setup_storing_service_registry,
)
from cg.services.orders.submitter.service import OrderSubmitter
from cg.services.orders.submitter.ticket_handler import TicketHandler
from cg.services.orders.validation.model_validator.model_validator import ModelValidator
from cg.services.orders.validation.service import OrderValidationService
from cg.store.store import Store
from tests.mocks.limsmock import MockLimsAPI


@pytest.fixture
def freshdesk_client() -> FreshdeskClient:
    return FreshdeskClient(base_url="https://mock.freshdesk.com", api_key="mock_api_key")


@pytest.fixture
def model_validator() -> ModelValidator:
    return ModelValidator()


@pytest.fixture
def order_validation_service(store_to_submit_and_validate_orders: Store) -> OrderValidationService:
    return OrderValidationService(
        lims_api=create_autospec(LimsAPI), store=store_to_submit_and_validate_orders
    )


@pytest.fixture(scope="function")
def order_submitter(
    ticket_handler: TicketHandler,
    storing_service_registry: StoringServiceRegistry,
    order_validation_service: OrderValidationService,
) -> OrderSubmitter:
    return OrderSubmitter(
        ticket_handler=ticket_handler,
        storing_registry=storing_service_registry,
        validation_service=order_validation_service,
    )


@pytest.fixture
def storing_service_registry(
    store_to_submit_and_validate_orders: Store, lims_api: MockLimsAPI
) -> StoringServiceRegistry:
    return setup_storing_service_registry(
        lims=lims_api, status_db=store_to_submit_and_validate_orders
    )


@pytest.fixture
def ticket_handler(store: Store, freshdesk_client: FreshdeskClient) -> TicketHandler:
    return TicketHandler(db=store, client=freshdesk_client, system_email_id=12345, env="production")
