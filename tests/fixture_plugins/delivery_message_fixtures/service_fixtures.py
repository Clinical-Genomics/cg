import pytest

from cg.services.delivery_message.delivery_message_service import DeliveryMessageService
from cg.store.models import Customer
from cg.store.store import Store
from tests.mocks.tb_mock import MockTB
from tests.store_helpers import StoreHelpers


@pytest.fixture
def delivery_message_store(store: Store, helpers: StoreHelpers) -> Store:
    """Returns a store with test cases for the delivery message test suite."""
    customer: Customer = helpers.ensure_customer(store=store)

    # Add two cases per workflow with: name, id, data delivery and ticket
    pass


@pytest.fixture
def delivery_message_service(trailblazer_api: MockTB) -> DeliveryMessageService:
    """Fixture for the delivery message service."""
    return DeliveryMessageService(trailblazer_api=trailblazer_api)
