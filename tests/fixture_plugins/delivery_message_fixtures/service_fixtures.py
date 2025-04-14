import pytest

from cg.services.delivery_message.delivery_message_service import DeliveryMessageService
from cg.store.models import Customer, Order
from cg.store.store import Store
from tests.mocks.tb_mock import MockTB
from tests.store_helpers import StoreHelpers


@pytest.fixture
def delivery_message_store(
    store: Store,
    helpers: StoreHelpers,
    delivery_cases: list[dict],
    customer_id: str,
    ticket_id_as_int: int,
) -> Store:
    """Returns a store with test cases for the delivery message test suite."""
    customer: Customer = helpers.ensure_customer(store=store, customer_id=customer_id)
    order: Order = helpers.add_order(
        store=store, customer_id=customer.id, ticket_id=ticket_id_as_int
    )
    for case_dict in delivery_cases:
        helpers.ensure_case(store=store, customer=customer, order=order, **case_dict)
    return store


@pytest.fixture
def delivery_message_service(
    delivery_message_store: Store, trailblazer_api: MockTB
) -> DeliveryMessageService:
    """Fixture for the delivery message service."""
    return DeliveryMessageService(store=delivery_message_store, trailblazer_api=trailblazer_api)
