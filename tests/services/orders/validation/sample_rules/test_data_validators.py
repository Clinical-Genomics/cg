from cg.services.orders.validation.constants import MAXIMUM_VOLUME
from cg.services.orders.validation.errors.sample_errors import (
    ApplicationArchivedError,
    ApplicationNotCompatibleError,
    ApplicationNotValidError,
    InvalidVolumeError,
)
from cg.services.orders.validation.order_types.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.order_types.microsalt.models.sample import MicrosaltSample
from cg.services.orders.validation.rules.sample.rules import (
    validate_application_compatibility,
    validate_application_exists,
    validate_applications_not_archived,
    validate_volume_interval,
)
from cg.store.models import Application
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


def test_application_is_incompatible(
    valid_microsalt_order: MicrosaltOrder,
    sample_with_non_compatible_application: MicrosaltSample,
    base_store: Store,
):

    # GIVEN an order that has a sample with an application which is incompatible with microsalt
    valid_microsalt_order.samples.append(sample_with_non_compatible_application)

    # WHEN validating the order
    errors = validate_application_compatibility(order=valid_microsalt_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the application compatability
    assert isinstance(errors[0], ApplicationNotCompatibleError)


def test_application_is_not_archived(
    valid_microsalt_order: MicrosaltOrder, archived_application: Application, base_store: Store
):

    # GIVEN an order with a new sample with an archived application
    valid_microsalt_order.samples[0].application = archived_application.tag
    base_store.session.add(archived_application)
    base_store.commit_to_store()

    # WHEN validating that the applications are not archived
    errors = validate_applications_not_archived(order=valid_microsalt_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the archived application
    assert isinstance(errors[0], ApplicationArchivedError)


def test_invalid_volume(valid_microsalt_order: MicrosaltOrder, base_store: Store):

    # GIVEN an order with a sample with an invalid volume
    valid_microsalt_order.samples[0].volume = MAXIMUM_VOLUME + 10

    # WHEN validating the volume interval
    errors = validate_volume_interval(order=valid_microsalt_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid volume
    assert isinstance(errors[0], InvalidVolumeError)
