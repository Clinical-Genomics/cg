from sqlalchemy.orm import Query

from cg.models.orders.constants import OrderType
from cg.store.filters.status_ordertype_application_filters import filter_applications_by_order_type
from cg.store.models import Application, OrderTypeApplication
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_filter_applications_by_order_type(applications_store: Store, helpers: StoreHelpers):
    # GIVEN a store with applications
    applications: list[Application] = applications_store.get_applications()
    assert applications

    # GIVEN an order type
    order_type = OrderType.PACBIO_LONG_READ

    # GIVEN that one application has the given order type
    helpers.add_application_order_type(
        store=applications_store, application=applications[0], order_types=[order_type]
    )

    # GIVEN that another application has a different order type
    helpers.add_application_order_type(
        store=applications_store, application=applications[1], order_types=[OrderType.BALSAMIC]
    )

    # WHEN filtering applications by order type
    order_type_applications: Query = applications_store._get_query(table=OrderTypeApplication)
    filtered_order_type_applications: Query = filter_applications_by_order_type(
        order_type_applications=order_type_applications, order_type=order_type
    )

    # THEN assert that only the applications with the given order type are returned
    assert filtered_order_type_applications.count() == 1
    assert filtered_order_type_applications.first().order_type == order_type
