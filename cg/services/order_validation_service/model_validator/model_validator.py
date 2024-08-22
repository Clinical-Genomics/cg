from pydantic_core import ValidationError
from cg.services.order_validation_service.errors.validation_errors import ValidationErrors
from cg.services.order_validation_service.model_validator.utils import convert_errors
from cg.services.order_validation_service.models.order import Order


class ModelValidator:

    @staticmethod
    def validate(order: dict, model: Order) -> tuple[Order | None, ValidationErrors]:
        try:
            order = model.model_validate(order)
            return order, ValidationErrors()
        except ValidationError as error:
            return None, convert_errors(pydantic_errors=error)
