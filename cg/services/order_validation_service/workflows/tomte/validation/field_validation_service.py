from typing import Tuple
from cg.services.order_validation_service.models.validation_error import ValidationErrors
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


class TomteFieldValidationService:

    def validate(self, order_json: str) -> Tuple[TomteOrder, ValidationErrors]:
        # TODO: map pydantic errors to ValidationErrors
        order = TomteOrder.model_validate_json(order_json)
        return order, ValidationErrors(errors=[])
