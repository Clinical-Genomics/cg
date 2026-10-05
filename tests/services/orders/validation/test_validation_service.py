import pytest

from cg.exc import OrderError
from cg.models.orders.constants import OrderType
from cg.services.orders.validation.service import OrderValidationService


def test_parse_and_validate_pydantic_error(
    order_validation_service: OrderValidationService, invalid_balsamic_order_to_submit: dict
):
    # GIVEN a raw order that will fail validation and a validation service

    # WHEN parsing and validating the order

    # THEN an OrderError should be raised
    with pytest.raises(OrderError):
        order_validation_service.parse_and_validate(
            raw_order=invalid_balsamic_order_to_submit,
            order_type=OrderType.BALSAMIC,
            user_id=1,
        )
