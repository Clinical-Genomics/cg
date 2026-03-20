from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.rna_fusion.constants import RNAFusionDeliveryType
from cg.services.orders.validation.order_types.rna_fusion.models.case import RNAFusionCase
from cg.services.orders.validation.order_types.rna_fusion.models.sample import RNAFusionSample


class RNAFusionOrder(OrderWithCases[RNAFusionCase, RNAFusionSample]):
    delivery_type: RNAFusionDeliveryType
