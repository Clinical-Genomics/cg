from cg.services.order_validation_service.models.errors import ValidationErrors
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


class TomteModelValidator:

    @classmethod
    def validate(cls, order_json: str) -> TomteOrder | ValidationErrors:
        return TomteOrder.model_validate_json(order_json)
