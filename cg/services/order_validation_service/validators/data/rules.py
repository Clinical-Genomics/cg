from cg.services.order_validation_service.models.errors import (
    ApplicationArchivedError,
    ApplicationNotValidError,
    CaseError,
    CaseSampleError,
    CustomerCannotSkipReceptionControlError,
    CustomerDoesNotExistError,
    InvalidGenePanelsError,
    OrderError,
    RepeatedGenePanelsError,
    UserNotAssociatedWithCustomerError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.data.utils import (
    contains_duplicates,
    validate_panels_for_case,
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
) -> list[OrderError]:
    errors: list[OrderError] = []

    if not order.skip_reception_control:
        return errors

    if not store.is_customer_trusted(order.customer_internal_id):
        error = CustomerCannotSkipReceptionControlError()
        errors.append(error)
    return errors


def validate_customer_exists(order: Order, store: Store, **kwargs) -> list[OrderError]:
    errors: list[OrderError] = []
    if not store.customer_exists(order.customer_internal_id):
        error = CustomerDoesNotExistError()
        errors.append(error)
    return errors


def validate_application_exists(order: TomteOrder, store: Store, **kwargs) -> list[CaseSampleError]:
    errors: list[CaseSampleError] = []
    for case in order.cases:
        for sample in case.samples:
            if not store.get_application_by_tag(sample.application):
                error = ApplicationNotValidError(case_name=case.name, sample_name=sample.name)
                errors.append(error)
    return errors


def validate_application_not_archived(
    order: TomteOrder, store: Store, **kwargs
) -> list[CaseSampleError]:
    errors: list[CaseSampleError] = []
    for case in order.cases:
        for sample in case.samples:
            if store.is_application_archived(sample.application):
                error = ApplicationArchivedError(case_name=case.name, sample_name=sample.name)
                errors.append(error)
    return errors


def validate_gene_panels_unique(order: TomteOrder, **kwargs) -> list[CaseError]:
    errors: list[CaseError] = []
    for case in order.cases:
        if contains_duplicates(case.panels):
            error = RepeatedGenePanelsError(case_name=case.name)
            errors.append(error)
    return errors


def validate_gene_panels_exist(
    order: TomteOrder, store: Store, **kwargs
) -> list[InvalidGenePanelsError]:
    errors: list[InvalidGenePanelsError] = []
    for case in order.cases:
        case_errors: list[InvalidGenePanelsError] = validate_panels_for_case(case=case, store=store)
        errors.extend(case_errors)
    return errors
