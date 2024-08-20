from cg.services.order_validation_service.errors.sample_errors import (
    ApplicationArchivedError,
    ApplicationNotValidError,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import (
    MicrosaltOrder,
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
