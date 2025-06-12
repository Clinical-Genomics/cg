import pytest

from cg.services.delivery_message.delivery_message_service import DeliveryMessageService
from cg.store.store import Store
from tests.mocks.tb_mock import MockTB


@pytest.fixture
def delivery_message_service(
    delivery_message_store: Store, trailblazer_api: MockTB
) -> DeliveryMessageService:
    """Fixture for the delivery message service."""
    return DeliveryMessageService(store=delivery_message_store, trailblazer_api=trailblazer_api)
