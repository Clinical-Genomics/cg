from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.balsamic_umi.constants import BalsamicUmiDeliveryType
from cg.services.orders.validation.order_types.balsamic_umi.models.case import BalsamicUmiCase
from cg.services.orders.validation.order_types.balsamic_umi.models.sample import BalsamicUmiSample


class BalsamicUmiOrder(OrderWithCases[BalsamicUmiCase, BalsamicUmiSample]):
    delivery_type: BalsamicUmiDeliveryType
