from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.nallo.constants import NalloDeliveryType
from cg.services.orders.validation.order_types.nallo.models.case import NalloCase
from cg.services.orders.validation.order_types.nallo.models.sample import NalloSample


class NalloOrder(OrderWithCases[NalloCase, NalloSample]):
    delivery_type: NalloDeliveryType
