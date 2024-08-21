from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.workflows.mip_dna.models.case import MipDnaCase


class MipDnaOrder(Order):
    cases: list[MipDnaCase]
