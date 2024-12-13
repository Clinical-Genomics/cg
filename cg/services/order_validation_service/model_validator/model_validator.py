from typing import TypeVar

from pydantic_core import ValidationError

from cg.services.order_validation_service.errors.validation_errors import ValidationErrors
from cg.services.order_validation_service.model_validator.utils import convert_errors
from cg.services.order_validation_service.models.order import Order

ParsedOrder = TypeVar("ParsedOrder", bound=Order)


class ModelValidator:

    @staticmethod
    def validate(order: dict, model: type[Order]) -> tuple[ParsedOrder | None, ValidationErrors]:
        try:
            order: Order = model.model_validate(order)
            return order, ValidationErrors()
        except ValidationError as error:
            return None, convert_errors(pydantic_errors=error)
