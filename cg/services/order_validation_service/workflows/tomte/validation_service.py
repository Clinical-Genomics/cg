from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


class TomteOrderValidationService:

    def __init__(self):
        pass

    def validate(self, order_json: str):
        order = TomteOrder.model_validate_json(order_json)
