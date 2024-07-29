from typing import Tuple

from pydantic import ValidationError

from cg.services.order_validation_service.models.errors import OrderError
from cg.services.order_validation_service.utils import convert_errors
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


class TomteFieldValidator:

    def validate(self, order_json: str) -> Tuple[TomteOrder, list[OrderError]]:
        try:
            return TomteOrder.model_validate_json(order_json)
        except ValidationError as error:
            order_errors: list[OrderError] = convert_errors(error.errors())
            return order_errors
