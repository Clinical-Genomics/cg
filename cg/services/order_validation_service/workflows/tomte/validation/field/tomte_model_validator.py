from pydantic_core import ValidationError

from cg.services.order_validation_service.models.errors import ValidationErrors
from cg.services.order_validation_service.validators.field.utils import convert_errors
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


class TomteModelValidator:

    @classmethod
    def validate(cls, raw_order: dict) -> tuple[TomteOrder | None, ValidationErrors]:
        try:
            order: TomteOrder = TomteOrder.model_validate(raw_order)
            return order, ValidationErrors()
        except ValidationError as error:
            return None, convert_errors(pydantic_errors=error)
