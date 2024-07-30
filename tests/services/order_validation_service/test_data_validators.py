from cg.services.order_validation_service.models.errors import ApplicationNotValidError
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.data.rules import (
    validate_application_exists,
)
from cg.store.store import Store


def test_applications_exist(valid_order: Order, base_store: Store):
    # GIVEN an order where one of the samples has an invalid application
    for case in valid_order.cases:
        case.samples[0].application = "Invalid application"

    # WHEN validating the order
    errors = validate_application_exists(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the ticket number
    assert isinstance(errors[0], ApplicationNotValidError)
