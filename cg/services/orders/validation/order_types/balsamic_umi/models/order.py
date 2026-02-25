from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.balsamic_umi.constants import BalsamicUmiDeliveryType


class BalsamicUmiOrder(BalsamicOrder):
    delivery_type: BalsamicUmiDeliveryType
