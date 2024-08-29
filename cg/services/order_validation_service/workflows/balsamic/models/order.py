from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.workflows.balsamic.models.case import BalsamicCase


class BalsamicOrder(OrderWithCases):
    cases: list[BalsamicCase]
