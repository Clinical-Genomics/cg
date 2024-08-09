from pydantic_core import ValidationError

from cg.services.order_validation_service.models.errors import ValidationErrors
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation.field.utils import (
    convert_errors,
)


class TomteModelValidator:

    def validate(self, order_json: str) -> tuple[TomteOrder | None, ValidationErrors]:
        try:
            order = TomteOrder.model_validate_json(order_json)
            return order, ValidationErrors()
        except ValidationError as error:
            return None, convert_errors(error)
