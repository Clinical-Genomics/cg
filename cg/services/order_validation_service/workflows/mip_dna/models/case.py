from cg.models.orders.samples import MipDnaSample
from cg.services.order_validation_service.models.case import Case


class MipDnaCase(Case):
    samples: list[MipDnaSample]
