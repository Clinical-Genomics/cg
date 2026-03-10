from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.tomte.constants import TomteDeliveryType
from cg.services.orders.validation.order_types.tomte.models.case import TomteCase


class TomteOrder(OrderWithCases[TomteCase]):
    delivery_type: TomteDeliveryType
