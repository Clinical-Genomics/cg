from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.errors.sample_errors import (
    ContainerNameMissingError,
    ContainerNameRepeatedError,
    SampleNameNotAvailableError,
    VolumeRequiredError,
    WellFormatError,
)
from cg.services.order_validation_service.rules.sample.rules import (
    validate_required_volume,
    validate_container_name_required,
    validate_sample_names_available,
    validate_tube_container_name_unique,
    validate_well_position_format,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import (
    MicrosaltOrder,
)
from cg.store.models import Sample
from cg.store.store import Store


def test_sample_names_available(valid_order: MicrosaltOrder, sample_store: Store):

    # GIVEN an order with a sample name reused from a previous order
    sample = sample_store.session.query(Sample).first()
    valid_order.customer = sample.customer.internal_id
    valid_order.samples[0].name = sample.name

    # WHEN validating that the sample names are available to the customer
    errors = validate_sample_names_available(order=valid_order, store=sample_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the reused sample name
    assert isinstance(errors[0], SampleNameNotAvailableError)


def test_validate_tube_container_name_unique(valid_order: MicrosaltOrder):

    # GIVEN an order with three samples in tubes with 2 reused container names
    valid_order.samples[0].container = ContainerEnum.tube
    valid_order.samples[1].container = ContainerEnum.tube
    valid_order.samples[2].container = ContainerEnum.tube
    valid_order.samples[0].container_name = "container_name"
    valid_order.samples[1].container_name = "container_name"
    valid_order.samples[2].container_name = "ContainerName"

    # WHEN validating the container names are unique
    errors = validate_tube_container_name_unique(order=valid_order)

    # THEN the error should concern the reused container name
    assert isinstance(errors[0], ContainerNameRepeatedError)
    assert errors[0].sample_index == 0
    assert errors[1].sample_index == 1


def test_validate_well_position_format(valid_order: MicrosaltOrder):

    # GIVEN an order with a sample with an invalid well position
    valid_order.samples[0].well_position = "J:4"

    # WHEN validating the well position format
    errors = validate_well_position_format(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid well position
    assert isinstance(errors[0], WellFormatError)
    assert errors[0].sample_index == 0


def test_validate_missing_container_name(valid_order: MicrosaltOrder):

    # GIVEN an order with a sample on a plate with no container name
    valid_order.samples[0].container = ContainerEnum.plate
    valid_order.samples[0].container_name = None

    # WHEN validating the container name
    errors = validate_container_name_required(order=valid_order)

    # THEN am error should be returned
    assert errors

    # THEN the error should concern the missing container name
    assert isinstance(errors[0], ContainerNameMissingError)
    assert errors[0].sample_index == 0


def test_validate_valid_container_name(valid_order: MicrosaltOrder):

    # GIVEN an order with a sample on a plate with a valid container name
    valid_order.samples[0].container = ContainerEnum.plate
    valid_order.samples[0].container_name = "Plate_123"

    # WHEN validating the container name
    errors = validate_container_name_required(order=valid_order)

    # THEN no error should be returned
    assert not errors


def test_validate_non_plate_container(valid_order: MicrosaltOrder):

    # GIVEN an order with missing container names but the samples are not on plates
    valid_order.samples[0].container = ContainerEnum.tube
    valid_order.samples[0].container_name = None

    valid_order.samples[1].container = ContainerEnum.no_container
    valid_order.samples[1].container_name = None

    # WHEN validating the container name
    errors = validate_container_name_required(order=valid_order)

    # THEN no error should be returned
    assert not errors


def test_missing_required_sample_volume(valid_order: MicrosaltOrder):

    # GIVEN an order with containerized samples missing volume
    valid_order.samples[0].container = ContainerEnum.tube
    valid_order.samples[0].volume = None

    valid_order.samples[1].container = ContainerEnum.plate
    valid_order.samples[1].volume = None

    # WHEN validating the volume
    errors = validate_required_volume(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid sample index
    assert isinstance(errors[0], VolumeRequiredError)
    assert errors[0].sample_index == 0

    assert isinstance(errors[1], VolumeRequiredError)
    assert errors[1].sample_index == 1


def test_non_required_sample_volume(valid_order: MicrosaltOrder):

    # GIVEN an order with a sample not in a container and with an invalid volume
    valid_order.samples[0].container = ContainerEnum.no_container
    valid_order.samples[0].volume = None

    # WHEN validating the volume
    errors = validate_required_volume(order=valid_order)

    # THEN an error should not be returned
    assert not errors
