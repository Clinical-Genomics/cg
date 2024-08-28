from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.workflows.mutant.models.sample import MutantSample


class MutantOrder(Order):
    samples: list[MutantSample]
