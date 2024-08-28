from cg.constants.constants import PrepCategory, Workflow
from cg.services.order_validation_service.constants import WORKFLOW_PREP_CATEGORIES
from cg.services.order_validation_service.errors.sample_errors import (
    ApplicationArchivedError,
    ApplicationNotCompatibleError,
    ApplicationNotValidError,
    ElutionBufferMissingError,
    ExtractionMethodMissingError,
    InvalidVolumeError,
    OccupiedWellError,
    OrganismDoesNotExistError,
    SampleNameRepeatedError,
)
from cg.services.order_validation_service.rules.utils import (
    is_application_not_compatible,
    is_volume_invalid,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import (
    MicrosaltOrder,
)
from cg.services.order_validation_service.workflows.microsalt.rules.sample.utils import (
    PlateSamplesValidator,
    get_indices_for_repeated_sample_names,
)
from cg.store.store import Store


def validate_application_exists(
    order: MicrosaltOrder, store: Store, **kwargs
) -> list[ApplicationNotValidError]:
    errors: list[ApplicationNotValidError] = []
    for sample_index, sample in order.enumerated_new_samples:
        if not store.get_application_by_tag(sample.application):
            error = ApplicationNotValidError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_applications_not_archived(
    order: MicrosaltOrder, store: Store, **kwargs
) -> list[ApplicationArchivedError]:
    errors: list[ApplicationArchivedError] = []
    for sample_index, sample in order.enumerated_new_samples:
        if store.is_application_archived(sample.application):
            error = ApplicationArchivedError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_volume_interval(order: MicrosaltOrder, **kwargs) -> list[InvalidVolumeError]:
    errors: list[InvalidVolumeError] = []
    for sample_index, sample in order.enumerated_new_samples:
        if is_volume_invalid(sample):
            error = InvalidVolumeError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_organism_exists(
    order: MicrosaltOrder, store: Store, **kwargs
) -> list[OrganismDoesNotExistError]:
    errors: list[OrganismDoesNotExistError] = []
    for sample_index, sample in order.enumerated_new_samples:
        if not store.get_organism_by_internal_id(sample.organism):
            error = OrganismDoesNotExistError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_buffer_required(order: MicrosaltOrder, **kwargs) -> list[ElutionBufferMissingError]:
    errors: list[ElutionBufferMissingError] = []
    for sample_index, sample in order.enumerated_new_samples:
        if not sample.elution_buffer:
            error = ElutionBufferMissingError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_extraction_method_required(
    order: MicrosaltOrder, **kwargs
) -> list[ExtractionMethodMissingError]:
    errors: list[ExtractionMethodMissingError] = []
    for sample_index, sample in order.enumerated_new_samples:
        if not sample.extraction_method:
            error = ExtractionMethodMissingError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_application_compatibility(
    order: MicrosaltOrder,
    store: Store,
    **kwargs,
) -> list[ApplicationNotCompatibleError]:
    errors: list[ApplicationNotCompatibleError] = []
    workflow: Workflow = order.workflow
    allowed_prep_categories: list[PrepCategory] = WORKFLOW_PREP_CATEGORIES[workflow]
    for sample_index, sample in order.enumerated_new_samples:
        incompatible: bool = is_application_not_compatible(
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
