from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation.field.tomte_model_validator import (
    TomteModelValidator,
)


def test_valid_order_is_parsed(
    valid_order: TomteOrder,
    tomte_model_validator: TomteModelValidator,
):
    # GIVEN a valid order
    order_json = valid_order.model_dump_json()

    # WHEN parsing the order
    order, errors = tomte_model_validator.validate(order_json)

    # THEN the parsed order is returned
    assert order is not None

    # THEN the errors are empty
    assert not errors.case_errors
    assert not errors.case_sample_errors
    assert not errors.order_errors
    assert not errors.sample_errors
