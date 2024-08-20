from pydantic_core import ValidationError
from cg.services.order_validation_service.errors.validation_errors import ValidationErrors
from cg.services.order_validation_service.validators.field.utils import convert_errors
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder


class MicroSaltModelValidator:

    @classmethod
    def validate(cls, raw_order: dict) -> tuple[MicrosaltOrder | None, ValidationErrors]:
        try:
            order = MicrosaltOrder.model_validate(raw_order)
            return order, ValidationErrors()
        except ValidationError as error:
            return None, convert_errors(pydantic_errors=error)
