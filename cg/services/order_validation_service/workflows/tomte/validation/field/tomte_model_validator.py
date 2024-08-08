from pydantic_core import ValidationError

from cg.services.order_validation_service.models.errors import ValidationErrors
from cg.services.order_validation_service.utils import convert_errors
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


class TomteModelValidator:

    @classmethod
    def validate(cls, order_json: str) -> tuple[TomteOrder | None, ValidationErrors]:
        try:
            order = TomteOrder.model_validate_json(order_json)
            return order, ValidationErrors()
        except ValidationError as error:
            return None, convert_errors(error)
