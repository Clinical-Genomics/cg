from cg.services.order_validation_service.models.errors import ValidationErrors
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

    # THEN no errors should be returned
    assert errors == ValidationErrors()
