from pydantic_core import ValidationError
from cg.services.order_validation_service.models.errors import ValidationErrors
from cg.services.order_validation_service.workflows.microsalt.models.order import MicroSaltOrder
from cg.services.order_validation_service.workflows.microsalt.validation.field.utils import (
    convert_errors,
)


class MicroSaltModelValidator:

    @classmethod
    def validate(cls, raw_order: dict) -> tuple[MicroSaltOrder | None, ValidationErrors]:
        try:
            order: MicroSaltOrder = MicroSaltOrder.model_validate(raw_order)
            return order, ValidationErrors()
        except ValidationError as error:
            return None, convert_errors(pydantic_errors=error)
