from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.workflows.tomte.constants import (
    TomteDeliveryType,
)
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase


class TomteOrder(OrderWithCases):
    cases: list[TomteCase]
    delivery_type: TomteDeliveryType
