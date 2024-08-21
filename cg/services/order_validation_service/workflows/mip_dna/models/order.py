from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.workflows.mip_dna.models.case import MipDnaCase


class MipDnaOrder(OrderWithCases):
    cases: list[MipDnaCase]
