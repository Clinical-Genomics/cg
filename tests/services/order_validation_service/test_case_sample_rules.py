from cg.models.orders.sample_base import ContainerEnum

from cg.services.order_validation_service.errors.case_sample_errors import (
    ContainerNameRepeatedError,
    WellFormatError,
)

from cg.services.order_validation_service.rules.case_sample.rules import (
    validate_tube_container_name_unique,
    validate_well_position_format,
)

from cg.services.order_validation_service.models.order_with_cases import (
    OrderWithCases,
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
