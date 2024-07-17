from typing import Tuple
from cg.services.order_validation_service.models.errors import OrderError
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


class TomteFieldValidator:

    def validate(self, order_json: str) -> Tuple[TomteOrder, list[OrderError]]:
        try:
            return TomteOrder.model_validate_json(order_json)
        except ValueError:
            # TODO: map all Pydantic errors to ValidationError
            pass
