from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.tomte.constants import TomteDeliveryType
from cg.services.orders.validation.order_types.tomte.models.case import TomteCase
from cg.services.orders.validation.order_types.tomte.models.sample import TomteSample


class TomteOrder(OrderWithCases[TomteCase, TomteSample]):
    delivery_type: TomteDeliveryType
