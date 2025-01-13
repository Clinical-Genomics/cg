from cg.services.order_validation_service.errors.sample_errors import MutantSampleNameNotUniqueError
from cg.services.order_validation_service.workflows.mutant.models.order import MutantOrder
from cg.services.order_validation_service.workflows.mutant.utils import (
    get_indices_for_repeated_non_control_sample_names,
)


def validate_non_control_samples_are_unique(
    order: MutantOrder,
) -> list[MutantSampleNameNotUniqueError]:
    """Validate that non-control samples are have unique names."""
    sample_indices: list[int] = get_indices_for_repeated_non_control_sample_names(order)
    return [
        MutantSampleNameNotUniqueError(sample_index=sample_index) for sample_index in sample_indices
    ]
