from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.workflows.mip_dna.models.sample import MipDnaSample


class MipDnaCase(Case):
    samples: list[MipDnaSample]
