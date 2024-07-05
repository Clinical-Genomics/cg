from cg.constants.constants import Workflow
from cg.services.order_validation_service.models.order import Order
from workflows.tomte.validation_service import TomteOrderValidationService


class OrderValidationService:
    """Service to orchestrate the order validation."""

    def __init__(self, tomte_service: TomteOrderValidationService):
        self.tomte_service = tomte_service

    def validate(self, order_json: str):
        order = Order.model_validate_json(order_json)

        if order.workflow == Workflow.TOMTE:
            self.tomte_service.validate(order_json)
