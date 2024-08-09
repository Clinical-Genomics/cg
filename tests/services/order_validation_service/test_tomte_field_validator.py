from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation.field.tomte_model_validator import (
    TomteModelValidator,
)


def test_valid_order_is_parsed(
    valid_order: TomteOrder,
    tomte_model_validator: TomteModelValidator,
):
    # GIVEN a valid order
    order = valid_order.model_dump(by_alias=True)

    # WHEN parsing the order
    order, errors = tomte_model_validator.validate(order)

    # THEN the parsed order is returned
    assert order

    # THEN the errors are empty
    assert not errors.case_errors
    assert not errors.case_sample_errors
    assert not errors.order_errors
    assert not errors.sample_errors


def test_order_field_error(
    valid_order: TomteOrder,
    tomte_model_validator: TomteModelValidator,
):
    pass


def test_case_field_error(
    valid_order: TomteOrder,
    tomte_model_validator: TomteModelValidator,
):
    pass


def test_sample_case_field_error(
    valid_order: TomteOrder,
    tomte_model_validator: TomteModelValidator,
):
    pass


def test_sample_field_error(
    valid_order: TomteOrder,
    tomte_model_validator: TomteModelValidator,
):
    pass
