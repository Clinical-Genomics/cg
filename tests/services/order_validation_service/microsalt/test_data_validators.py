from cg.services.order_validation_service.errors.sample_errors import (
    ApplicationNotValidError,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import (
    MicrosaltOrder,
)
from cg.services.order_validation_service.workflows.microsalt.validation.data.rules import (
    validate_application_exists,
)
from cg.store.store import Store


def test_applications_exist_sample_order(valid_microsalt_order: MicrosaltOrder, base_store: Store):

    # GIVEN an order with a sample with an application which is not found in the database
    valid_microsalt_order.samples[0].application = "Non-existent app tag"

    # WHEN validating that the specified applications exist
    errors = validate_application_exists(order=valid_microsalt_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid application
    assert isinstance(errors[0], ApplicationNotValidError)


def test_application_is_compatible():
    pass
