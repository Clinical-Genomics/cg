from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.mip_rna.constants import MIPRNADeliveryType
from cg.services.orders.validation.order_types.mip_rna.models.case import MIPRNACase
from cg.services.orders.validation.order_types.mip_rna.models.sample import MIPRNASample


class MIPRNAOrder(OrderWithCases[MIPRNACase, MIPRNASample]):
    delivery_type: MIPRNADeliveryType
