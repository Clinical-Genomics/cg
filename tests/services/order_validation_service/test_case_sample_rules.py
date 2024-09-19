from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.errors.case_sample_errors import (
    ContainerNameRepeatedError,
    VolumeRequiredCaseError,
    WellFormatError,
)
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.rules.case_sample.rules import (
    validate_required_volume,
    validate_tube_container_name_unique,
    validate_well_position_format,
)


def test_validate_well_position_format(valid_order: OrderWithCases):

    # GIVEN an order with invalid well position format
    valid_order.cases[0].samples[0].well_position = "D:0"

    # WHEN validating the well position format
    errors = validate_well_position_format(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the invalid well position format
    assert isinstance(errors[0], WellFormatError)
    assert errors[0].sample_index == 0 and errors[0].case_index == 0


def test_validate_tube_container_name_unique(valid_order: OrderWithCases):

    # GIVEN an order with two samples with the same tube container name
    valid_order.cases[0].samples[0].container = ContainerEnum.tube
    valid_order.cases[0].samples[1].container = ContainerEnum.tube
    valid_order.cases[0].samples[0].container_name = "tube_name"
    valid_order.cases[0].samples[1].container_name = "tube_name"

    # WHEN validating the tube container name uniqueness
    errors = validate_tube_container_name_unique(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the non-unique tube container name
    assert isinstance(errors[0], ContainerNameRepeatedError)
    assert errors[0].sample_index == 0 and errors[0].case_index == 0


def test_missing_required_volume(valid_order: OrderWithCases):

    # GIVEN an orders with two samples with missing volumes
    valid_order.cases[0].samples[0].container = ContainerEnum.tube
    valid_order.cases[0].samples[0].volume = None

    valid_order.cases[0].samples[1].container = ContainerEnum.plate
    valid_order.cases[0].samples[1].volume = None

    # WHEN validating that required volumes are set
    errors: list[VolumeRequiredCaseError] = validate_required_volume(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the missing volumes
    assert isinstance(errors[0], VolumeRequiredCaseError)
    assert errors[0].sample_index == 0 and errors[0].case_index == 0

    assert isinstance(errors[1], VolumeRequiredCaseError)
    assert errors[1].sample_index == 1 and errors[1].case_index == 0


def test_missing_volume_no_container(valid_order: OrderWithCases):

    # GIVEN an order with a sample with missing volume, but which is in no container
    valid_order.cases[0].samples[0].container = ContainerEnum.no_container
    valid_order.cases[0].samples[0].volume = None

    # WHEN validating that the order has required volumes set
    errors: list[VolumeRequiredCaseError] = validate_required_volume(order=valid_order)

    # THEN no error should be returned
    assert not errors
