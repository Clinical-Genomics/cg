import pytest

from cg.exc import OrderError

from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import ControlEnum
from cg.models.orders.samples import SarsCov2Sample
from cg.services.orders.validate_order_services.validate_microbial_order import (
    ValidateMicrobialOrderService,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_validate_normal_order(sarscov2_order_to_submit: dict, base_store: Store):
    # GIVEN sarscov2 order with three samples, none in the database
    order = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    # WHEN validating the order
    ValidateMicrobialOrderService(base_store).validate_order(order=order)
    # THEN it should be regarded as valid


def test_validate_submitted_order(
    sarscov2_order_to_submit: dict, base_store: Store, helpers: StoreHelpers
):
    # GIVEN sarscov2 order with three samples, all in the database
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    sample: SarsCov2Sample
    for sample in order.samples:
        helpers.add_sample(store=base_store, customer_id=order.customer, name=sample.name)

    # WHEN validating the order
    # THEN it should be regarded as invalid
    with pytest.raises(OrderError):
        ValidateMicrobialOrderService(base_store).validate_order(order=order)


def test_validate_submitted_control_order(
    sarscov2_order_to_submit: dict, base_store: Store, helpers: StoreHelpers
):
    # GIVEN sarscov2 order with three control samples, all in the database
    order: OrderIn = OrderIn.parse_obj(sarscov2_order_to_submit, OrderType.SARS_COV_2)

    sample: SarsCov2Sample
    for sample in order.samples:
        helpers.add_sample(store=base_store, customer_id=order.customer, name=sample.name)
        sample.control = ControlEnum.positive

    # WHEN validating the order
    # THEN it should be regarded as valid
    ValidateMicrobialOrderService(base_store).validate_order(order=order)


def test_validate_microbial_fast_order(microbial_fastq_order_to_submit: dict, base_store: Store):
    # GIVEN a microbial order with three samples, none in the database

    # WHEN validating the order
    order = OrderIn.parse_obj(microbial_fastq_order_to_submit, OrderType.MICROBIAL_FASTQ)

    # THEN it should be regarded as valid
    ValidateMicrobialOrderService(base_store).validate_order(order=order)
