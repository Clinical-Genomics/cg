from collections import Counter

from cg.constants.constants import PrepCategory, Workflow
from cg.services.order_validation_service.constants import WORKFLOW_PREP_CATEGORIES
from cg.services.order_validation_service.errors.sample_errors import (
    ApplicationNotCompatibleError,
    OccupiedWellError,
    SampleNameRepeatedError,
)
from cg.services.order_validation_service.validators.inter_field.utils import (
    _is_application_not_compatible,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import (
    MicrosaltOrder,
)
from cg.services.order_validation_service.workflows.microsalt.validation.inter_field.utils import (
    PlateSamplesValidator,
)
from cg.store.store import Store


def validate_application_compatibility(
    order: MicrosaltOrder,
    store: Store,
    **kwargs,
) -> list[ApplicationNotCompatibleError]:
    errors: list[ApplicationNotCompatibleError] = []
    workflow: Workflow = order.workflow
    allowed_prep_categories: list[PrepCategory] = WORKFLOW_PREP_CATEGORIES[workflow]
    for sample_index, sample in order.enumerated_new_samples:
        incompatible: bool = _is_application_not_compatible(
            allowed_prep_categories=allowed_prep_categories,
            application_tag=sample.application,
            store=store,
        )
        if incompatible:
            error = ApplicationNotCompatibleError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_wells_contain_at_most_one_sample(
    order: MicrosaltOrder,
    **kwargs,
) -> list[OccupiedWellError]:
    plate_samples = PlateSamplesValidator(order)
    return plate_samples.get_occupied_well_errors()


def validate_well_positions_required(
    order: MicrosaltOrder,
    **kwargs,
) -> list[OccupiedWellError]:
    plate_samples = PlateSamplesValidator(order)
    return plate_samples.get_well_position_missing_errors()


def validate_sample_names_unique(order: MicrosaltOrder, **kwargs) -> list[SampleNameRepeatedError]:
    sample_indices: list[int] = get_indices_for_repeated_sample_names(order)
    return [SampleNameRepeatedError(sample_index=sample_index) for sample_index in sample_indices]


def get_indices_for_repeated_sample_names(order: MicrosaltOrder) -> list[int]:
    counter = Counter([sample.name for sample in order.samples])
    indices: list[int] = []
    for index, sample in order.enumerated_new_samples:
        if counter.get(sample.name) > 1:
            indices.append(index)
    return indices
