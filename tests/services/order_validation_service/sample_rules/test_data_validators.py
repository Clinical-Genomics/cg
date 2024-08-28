from cg.services.order_validation_service.constants import MAXIMUM_VOLUME
from cg.services.order_validation_service.errors.sample_errors import (
    ApplicationArchivedError,
    ApplicationNotCompatibleError,
    ApplicationNotValidError,
    ElutionBufferMissingError,
    ExtractionMethodMissingError,
    InvalidVolumeError,
    OrganismDoesNotExistError,
)
from cg.services.order_validation_service.rules.sample.rules import (
    validate_application_compatibility,
    validate_application_exists,
    validate_applications_not_archived,
    validate_buffer_required,
    validate_extraction_method_required,
    validate_organism_exists,
    validate_volume_interval,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import (
    MicrosaltOrder,
)
from cg.services.order_validation_service.workflows.microsalt.models.sample import (
    MicrosaltSample,
)
from cg.store.models import Application
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


def test_application_is_not_archived(
    valid_order: MicrosaltOrder, archived_application: Application, base_store: Store
):

    # GIVEN an order with a new sample with an archived application
    valid_order.samples[0].application = archived_application.tag
    base_store.session.add(archived_application)
    base_store.commit_to_store()

    # WHEN validating that the applications are not archived
    errors = validate_applications_not_archived(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the archived application
    assert isinstance(errors[0], ApplicationArchivedError)


def test_invalid_volume(valid_order: MicrosaltOrder, base_store: Store):

    # GIVEN an order with a sample with an invalid volume
    valid_order.samples[0].volume = MAXIMUM_VOLUME + 10

    # WHEN validating the volume interval
    errors = validate_volume_interval(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid volume
    assert isinstance(errors[0], InvalidVolumeError)


def test_invalid_organism(valid_order: MicrosaltOrder, base_store: Store):

    # GIVEN an order with a sample specifying a non-existent organism
    valid_order.samples[0].organism = "Non-existent organism"

    # WHEN validating that all organisms exist
    errors = validate_organism_exists(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid organism
    assert isinstance(errors[0], OrganismDoesNotExistError)


def test_valid_organisms(valid_order: MicrosaltOrder, base_store: Store):

    # GIVEN a valid order

    # WHEN validating that all organisms exist
    errors = validate_organism_exists(order=valid_order, store=base_store)

    # THEN no error should be returned
    assert not errors


def test_buffer_required(valid_order: MicrosaltOrder):

    # GIVEN an order containing a sample with missing buffer
    valid_order.samples[0].elution_buffer = None

    # WHEN validating that buffers are set for new samples
    errors = validate_buffer_required(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing buffer
    assert isinstance(errors[0], ElutionBufferMissingError)


def test_extraction_method_missing(valid_order: MicrosaltOrder):

    # GIVEN an order containing a sample with missing extraction method
    valid_order.samples[0].extraction_method = None

    # WHEN validating that the extraction method is set for all new samples
    errors = validate_extraction_method_required(order=valid_order)

    # THEN an error should be raised
    assert errors

    # THEN the error should concern the missing extraction method
    assert isinstance(errors[0], ExtractionMethodMissingError)
