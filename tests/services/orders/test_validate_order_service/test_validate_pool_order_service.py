import pytest

from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.exc import OrderError
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.samples import RmlSample
from cg.services.orders.validate_order_services.validate_pool_order import ValidatePoolOrderService
from cg.store.models import Customer
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_validate_normal_order(rml_order_to_submit: dict, base_store: Store):
    # GIVEN pool order with three samples, none in the database
    order = OrderIn.parse_obj(rml_order_to_submit, OrderType.RML)

    # WHEN validating the order
    ValidatePoolOrderService(status_db=base_store).validate_order(order=order)
    # THEN it should be regarded as valid


def test_validate_case_name(rml_order_to_submit: dict, base_store: Store, helpers: StoreHelpers):
    # GIVEN pool order with a case already all in the database
    order: OrderIn = OrderIn.parse_obj(rml_order_to_submit, OrderType.RML)

    sample: RmlSample
    customer: Customer = helpers.ensure_customer(store=base_store, customer_id=order.customer)
    for sample in order.samples:
        case = helpers.ensure_case(
            store=base_store,
            case_name=ValidatePoolOrderService.create_case_name(
                ticket=order.ticket, pool_name=sample.pool
            ),
            customer=customer,
            data_analysis=Workflow.FLUFFY,
            data_delivery=DataDelivery.STATINA,
        )
        base_store.session.add(case)
        base_store.session.commit()

    # WHEN validating the order
    # THEN it should be regarded as invalid
    with pytest.raises(OrderError):
        ValidatePoolOrderService(status_db=base_store).validate_order(order=order)
