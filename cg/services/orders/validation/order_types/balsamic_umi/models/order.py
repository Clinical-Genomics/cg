from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.balsamic_umi.constants import BalsamicUmiDeliveryType
from cg.services.orders.validation.order_types.balsamic_umi.models.case import BalsamicUmiCase


class BalsamicUmiOrder(OrderWithCases[BalsamicUmiCase]):
    delivery_type: BalsamicUmiDeliveryType
