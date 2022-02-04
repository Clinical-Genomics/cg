import pytest

from cg.exc import OrderError
from cg.meta.orders.sars_cov_2_submitter import SarsCov2Submitter
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import ControlEnum
from cg.models.orders.samples import SarsCov2Sample
from cg.store import Store
from tests.store_helpers import StoreHelpers


def test_validate_normal_order(sarscov2_order_to_submit: dict, base_store: Store):
    # GIVEN sarscov2 order with three samples, none in the database
    order = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    # WHEN validating the order
    SarsCov2Submitter(status=base_store, lims=None).validate_order(order=order)
    # THEN it should be regarded as valid


def test_validate_submitted_order(
    sarscov2_order_to_submit: dict, base_store: Store, helpers: StoreHelpers
):
    # GIVEN sarscov2 order with three samples, all in the database
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    sample: SarsCov2Sample
    for sample in order.samples:
        helpers.add_sample(store=base_store, name=sample.name, customer_id=order.customer)

    # WHEN validating the order
    # THEN it should be regarded as invalid
    with (pytest.raises(OrderError)):
        SarsCov2Submitter(status=base_store, lims=None).validate_order(order=order)


def test_validate_submitted_control_order(
    sarscov2_order_to_submit: dict, base_store: Store, helpers: StoreHelpers
):
    # GIVEN sarscov2 order with three control samples, all in the database
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    sample: SarsCov2Sample
    for sample in order.samples:
        helpers.add_sample(store=base_store, name=sample.name, customer_id=order.customer)
        sample.control = ControlEnum.positive

    # WHEN validating the order
    # THEN it should be regarded as valid
    SarsCov2Submitter(status=base_store, lims=None).validate_order(order=order)
