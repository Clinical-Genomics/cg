from cg.services.order_validation_service.models.errors import (
    ApplicationArchivedError,
    ApplicationNotValidError,
    CustomerCannotSkipReceptionControlError,
    CustomerDoesNotExistError,
    InvalidGenePanelsError,
    InvalidVolumeError,
    OrderError,
    RepeatedGenePanelsError,
    UserNotAssociatedWithCustomerError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.data.utils import (
    contains_duplicates,
    get_invalid_panels,
    is_volume_invalid,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.store.store import Store


def validate_user_belongs_to_customer(order: Order, store: Store, **kwargs) -> list[OrderError]:
    has_access: bool = store.is_user_associated_with_customer(
        user_id=order.user_id,
        customer_internal_id=order.customer_internal_id,
    )

    errors: list[OrderError] = []
    if not has_access:
        error = UserNotAssociatedWithCustomerError()
        errors.append(error)
    return errors


def validate_customer_can_skip_reception_control(
    order: Order, store: Store, **kwargs
) -> list[CustomerCannotSkipReceptionControlError]:
    errors: list[CustomerCannotSkipReceptionControlError] = []

    if not order.skip_reception_control:
        return errors

    if not store.is_customer_trusted(order.customer_internal_id):
        error = CustomerCannotSkipReceptionControlError()
        errors.append(error)
    return errors


def validate_customer_exists(
    order: Order, store: Store, **kwargs
) -> list[CustomerDoesNotExistError]:
    errors: list[CustomerDoesNotExistError] = []
    if not store.customer_exists(order.customer_internal_id):
        error = CustomerDoesNotExistError()
        errors.append(error)
    return errors


def validate_application_exists(
    order: TomteOrder, store: Store, **kwargs
) -> list[ApplicationNotValidError]:
    errors: list[ApplicationNotValidError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not store.get_application_by_tag(sample.application):
                error = ApplicationNotValidError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_application_not_archived(
    order: TomteOrder, store: Store, **kwargs
) -> list[ApplicationArchivedError]:
    errors: list[ApplicationArchivedError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if store.is_application_archived(sample.application):
                error = ApplicationArchivedError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_gene_panels_unique(order: TomteOrder, **kwargs) -> list[RepeatedGenePanelsError]:
    errors: list[RepeatedGenePanelsError] = []
    for case_index, case in order.enumerated_new_cases:
        if contains_duplicates(case.panels):
            error = RepeatedGenePanelsError(case_index=case_index)
            errors.append(error)
    return errors


def validate_gene_panels_exist(
    order: TomteOrder, store: Store, **kwargs
) -> list[InvalidGenePanelsError]:
    errors: list[InvalidGenePanelsError] = []
    for case_index, case in order.enumerated_new_cases:
        if invalid_panels := get_invalid_panels(panels=case.panels, store=store):
            case_error = InvalidGenePanelsError(case_index=case_index, panels=invalid_panels)
            errors.append(case_error)
    return errors


def validate_volume_interval(order: TomteOrder) -> list[InvalidVolumeError]:
    errors: list[InvalidVolumeError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_volume_invalid(sample):
                error = InvalidVolumeError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors
