from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.raredisease.constants import RarediseaseDeliveryType
from cg.services.orders.validation.order_types.raredisease.models.case import RarediseaseCase


class RarediseaseOrder(OrderWithCases[RarediseaseCase]):
    delivery_type: RarediseaseDeliveryType
