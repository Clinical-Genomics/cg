import pytest

from cg.models.orders.constants import OrderType
from cg.store.exc import EntryNotFoundError
from cg.store.models import Application
from cg.store.store import Store


def test_get_active_applications_by_order_type_no_application(store: Store):
    """Test that if there are not applications for a given type an error is raised."""
    # GIVEN a store with applications without order types
    applications: list[Application] = store.get_applications()
    for application in applications:
        assert not application.order_types

    # GIVEN an order type
    order_type: OrderType = OrderType.PACBIO_LONG_READ

    # WHEN getting active applications by order type
    with pytest.raises(EntryNotFoundError):
        store.get_active_applications_by_order_type(order_type)

    # THEN an EntryNotFoundError is raised
