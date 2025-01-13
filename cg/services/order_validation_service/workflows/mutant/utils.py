from collections import Counter

from cg.models.orders.sample_base import ControlEnum
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder


def get_indices_for_repeated_non_control_sample_names(order: MutantOrder) -> list[int]:
    counter = Counter(
        [sample.name for sample in order.samples if sample.control == ControlEnum.not_control]
    )
    indices: list[int] = []
    for index, sample in order.enumerated_samples:
        if counter.get(sample.name) > 1 and sample.control == ControlEnum.not_control:
            indices.append(index)
    return indices
