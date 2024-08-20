from cg.services.order_validation_service.errors.sample_errors import (
    ApplicationNotValidError,
    ApplicationNotCompatibleError,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import (
    MicrosaltOrder,
)
from cg.services.order_validation_service.workflows.microsalt.models.sample import MicrosaltSample
from cg.services.order_validation_service.workflows.microsalt.validation.data.rules import (
    validate_application_exists,
)
from cg.services.order_validation_service.workflows.microsalt.validation.inter_field.rules import (
    validate_application_compatibility,
)
from cg.store.store import Store


def test_applications_exist_sample_order(valid_order: MicrosaltOrder, base_store: Store):

    # GIVEN an order with a sample with an application which is not found in the database
    valid_order.samples[0].application = "Non-existent app tag"

    # WHEN validating that the specified applications exist
    errors = validate_application_exists(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid application
    assert isinstance(errors[0], ApplicationNotValidError)


def test_application_is_incompatible(
    valid_order: MicrosaltOrder,
    sample_with_non_compatible_application: MicrosaltSample,
    base_store: Store,
):

    # GIVEN an order that has a sample with an application which is incompatible with microsalt
    valid_order.samples.append(sample_with_non_compatible_application)

    # WHEN validating the order
    errors = validate_application_compatibility(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the application compatability
    assert isinstance(errors[0], ApplicationNotCompatibleError)
