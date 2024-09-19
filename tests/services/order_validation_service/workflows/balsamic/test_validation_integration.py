from cg.services.order_validation_service.workflows.balsamic.models.order import (
    BalsamicOrder,
)
from cg.services.order_validation_service.workflows.balsamic.validation_service import (
    BalsamicValidationService,
)


def test_valid_order(
    valid_order: BalsamicOrder, balsamic_validation_service: BalsamicValidationService
):

    # GIVEN a valid order

    # WHEN validating the order
    errors = balsamic_validation_service._get_errors(valid_order.model_dump())

    # THEN no errors should be raised
    assert not errors.order_errors
    assert not errors.case_errors
    assert not errors.case_sample_errors


def test_valid_order_conversion(
    valid_order: BalsamicOrder, balsamic_validation_service: BalsamicValidationService
):

    # GIVEN a valid order
    order: dict = valid_order.model_dump()

    # WHEN validating the order
    response = balsamic_validation_service.validate(order)

    # THEN a response should be given
    assert response


def test_order_error_conversion(
    valid_order: BalsamicOrder, balsamic_validation_service: BalsamicValidationService
):

    # GIVEN an order with a missing field on order level
    valid_order.name = ""
    order: dict = valid_order.model_dump()

    # WHEN validating the order
    response: dict = balsamic_validation_service.validate(order)

    # THEN there should be an error for the missing name
    assert response["name"]["errors"]


def test_case_error_conversion(
    valid_order: BalsamicOrder, balsamic_validation_service: BalsamicValidationService
):

    # GIVEN an order with a faulty case priority
    valid_order.cases[0].priority = "Non-existent priority"
    order = valid_order.model_dump()

    # WHEN validating the order
    response: dict = balsamic_validation_service.validate(order)

    # THEN there should be an error for the faulty priority
    assert response["cases"][0]["priority"]["errors"]


def test_sample_error_conversion(
    valid_order: BalsamicOrder, balsamic_validation_service: BalsamicValidationService
):

    # GIVEN an order with a sample with an invalid field
    valid_order.cases[0].samples[0].volume = 1
    invalid_order: dict = valid_order.model_dump()

    # WHEN validating the order
    response = balsamic_validation_service.validate(invalid_order)

    # THEN an error should be returned regarding the invalid volume
    assert response["cases"][0]["samples"][0]["volume"]["errors"]
