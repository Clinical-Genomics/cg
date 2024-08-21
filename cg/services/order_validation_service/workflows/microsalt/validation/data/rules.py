from cg.services.order_validation_service.errors.sample_errors import (
    ApplicationArchivedError,
    ApplicationNotValidError,
    ElutionBufferMissingError,
    ExtractionMethodMissingError,
    InvalidVolumeError,
    OrganismDoesNotExistError,
    SampleDoesNotExistError,
)
from cg.services.order_validation_service.validators.data.utils import is_volume_invalid
from cg.services.order_validation_service.workflows.microsalt.models.order import (
    MicrosaltOrder,
)
from cg.store.models import Sample
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


def validate_samples_exist(
    order: MicrosaltOrder, store: Store, **kwargs
) -> list[SampleDoesNotExistError]:
    errors: list[SampleDoesNotExistError] = []
    for sample_index, sample in order.enumerated_existing_samples:
        sample: Sample | None = store.get_sample_by_internal_id(sample.internal_id)
        if not sample:
            error = SampleDoesNotExistError(sample_index=sample_index)
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
