import pytest

from cg.models.orders.constants import OrderType
from cg.store.exc import EntryNotFoundError
from cg.store.models import Application
from cg.store.store import Store


def test_get_active_applications_by_order_type(store_with_applications_with_order_types: Store):
    """Test that getting non-archived applications by order type works."""
    # GIVEN a store with applications with different order types
    store: Store = store_with_applications_with_order_types
    number_applications: int = len(store.get_applications())
    assert number_applications > 0

    # GIVEN an order type
    order_type: OrderType = OrderType.PACBIO_LONG_READ

    # WHEN getting active applications by order type
    applications: list[Application] = store.get_active_applications_by_order_type(order_type)

    # THEN assert that only the applications with the given order type are returned
    assert number_applications > len(applications) > 0
    for application in applications:
        app_order_types: list[OrderType] = [link.order_type for link in application.order_types]
        assert order_type in app_order_types


def test_get_active_applications_by_order_type_no_application(store):
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
