import pytest

from cg.exc import OrderError
from cg.models.orders.order import OrderIn
from cg.services.orders.validate_order_services.validate_pacbio_order import (
    ValidatePacbioOrderService,
)
from cg.store.store import Store


def test_validate_valid_pacbio_order(
    validate_pacbio_order_service: ValidatePacbioOrderService, pacbio_order: OrderIn
):
    # GIVEN a valid PacBio order

    # WHEN validating the order
    validate_pacbio_order_service.validate_order(pacbio_order)

    # THEN no error is raised


def test_validate_pacbio_order_unknown_customer(
    pacbio_order: OrderIn, validate_pacbio_order_service: ValidatePacbioOrderService
):
    # GIVEN a PacBio order with an unknown customer
    pacbio_order.customer = "unknown_customer"

    # WHEN validating the order

    # THEN an order error should be raised
    with pytest.raises(OrderError):
        validate_pacbio_order_service.validate_order(pacbio_order)


def test_validate_pacbio_order_invalid_application(
    pacbio_order: OrderIn, validate_pacbio_order_service: ValidatePacbioOrderService
):
    # GIVEN a PacBio order with an unknown application
    pacbio_order.samples[0].application = "unknown_application"

    # WHEN validating the order

    # THEN an order error should be raised
    with pytest.raises(OrderError):
        validate_pacbio_order_service.validate_order(pacbio_order)


def test_validate_pacbio_order_reused_sample_name(
    pacbio_order: OrderIn, validate_pacbio_order_service: ValidatePacbioOrderService
):
    # GIVEN a PacBio order with a reused sample name
    status_db: Store = validate_pacbio_order_service.status_db
    customer = status_db.get_customer_by_internal_id(pacbio_order.customer)
    old_sample_name: str = status_db.get_samples_by_customers_and_pattern(customers=[customer])[
        0
    ].name
    pacbio_order.samples[0].name = old_sample_name

    # WHEN validating the order

    # THEN an order error should be raised
    with pytest.raises(OrderError):
        validate_pacbio_order_service.validate_order(pacbio_order)
