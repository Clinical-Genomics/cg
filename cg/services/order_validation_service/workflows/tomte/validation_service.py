from cg.services.order_validation_service.models.validation_error import ValidationErrors
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


class TomteValidationService(OrderValidationService):

    def validate(self, order_json: str) -> ValidationErrors:
        TomteOrder.model_validate(order_json)
