from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.rna_fusion.constants import RNAFusionDeliveryType
from cg.services.orders.validation.order_types.rna_fusion.models.case import RNAFusionCase


class RNAFusionOrder(OrderWithCases[RNAFusionCase]):
    delivery_type: RNAFusionDeliveryType
