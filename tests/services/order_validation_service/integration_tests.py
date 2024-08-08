from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation_service import (
    TomteValidationService,
)


def test_valid_order(valid_order: TomteOrder, tomte_validation_service: TomteValidationService):

    # GIVEN a valid order

    # WHEN validating the order
    errors = tomte_validation_service.validate(valid_order.model_dump_json())

    # THEN no errors should be raised
    assert not errors
