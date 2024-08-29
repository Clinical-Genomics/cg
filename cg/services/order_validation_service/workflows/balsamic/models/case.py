from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.workflows.balsamic.models.sample import BalsamicSample


class BalsamicCase(Case):
    samples: list[BalsamicSample]
