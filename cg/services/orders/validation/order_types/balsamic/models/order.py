from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.balsamic.constants import BalsamicDeliveryType
from cg.services.orders.validation.order_types.balsamic.models.case import BalsamicCase


class BalsamicOrder(OrderWithCases[BalsamicCase]):
    delivery_type: BalsamicDeliveryType
