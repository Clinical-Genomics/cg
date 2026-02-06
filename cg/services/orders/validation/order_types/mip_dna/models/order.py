from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.order_types.mip_dna.constants import MIPDNADeliveryType
from cg.services.orders.validation.order_types.mip_dna.models.case import MIPDNACase


class MIPDNAOrder(OrderWithCases[MIPDNACase]):
    delivery_type: MIPDNADeliveryType
