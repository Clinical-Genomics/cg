from cg.services.order_validation_service.models.errors import (
    ApplicationArchivedError,
    ApplicationNotValidError,
    CustomerCannotSkipReceptionControlError,
    CustomerDoesNotExistError,
    OrderError,
    SampleError,
    UserNotAssociatedWithCustomerError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.data.utils import (
    is_application_archived,
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


def validate_application_exists(order: TomteOrder, store: Store, **kwargs) -> list[SampleError]:
    errors: list[SampleError] = []
    for case in order.cases:
        for sample in case.samples:
            if not store.get_application_by_tag(sample.application):
                error = ApplicationNotValidError(case_name=case.name, sample_name=sample.name)
                errors.append(error)
    return errors


def validate_application_not_archived(
    order: TomteOrder, store: Store, **kwargs
) -> list[SampleError]:
    errors: list[SampleError] = []
    for case in order.cases:
        for sample in case.samples:
            if is_application_archived(application_tag=sample.application, store=store):
                error = ApplicationArchivedError(case_name=case.name, sample_name=sample.name)
                errors.append(error)
    return errors
