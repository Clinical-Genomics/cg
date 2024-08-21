from cg.services.order_validation_service.errors.case_errors import (
    CaseDoesNotExistError,
    CaseNameNotAvailableError,
    InvalidGenePanelsError,
    RepeatedGenePanelsError,
)
from cg.services.order_validation_service.errors.case_sample_errors import (
    ApplicationArchivedError,
    ApplicationNotValidError,
    InvalidVolumeError,
    SampleDoesNotExistError,
    SexMissingError,
    SourceMissingError,
)
from cg.services.order_validation_service.errors.order_errors import (
    CustomerCannotSkipReceptionControlError,
    CustomerDoesNotExistError,
    OrderError,
    UserNotAssociatedWithCustomerError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.validators.data.utils import (
    contains_duplicates,
    get_invalid_panels,
    is_volume_invalid,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


def validate_user_belongs_to_customer(order: Order, store: Store, **kwargs) -> list[OrderError]:
    has_access: bool = store.is_user_associated_with_customer(
        user_id=order.user_id,
        customer_internal_id=order.customer,
    )

    errors: list[OrderError] = []
    if not has_access:
        error = UserNotAssociatedWithCustomerError()
        errors.append(error)
    return errors


def validate_customer_can_skip_reception_control(
    order: Order,
    store: Store,
    **kwargs,
) -> list[CustomerCannotSkipReceptionControlError]:
    errors: list[CustomerCannotSkipReceptionControlError] = []

    if not order.skip_reception_control:
        return errors

    if not store.is_customer_trusted(order.customer):
        error = CustomerCannotSkipReceptionControlError()
        errors.append(error)
    return errors


def validate_customer_exists(
    order: Order,
    store: Store,
    **kwargs,
) -> list[CustomerDoesNotExistError]:
    errors: list[CustomerDoesNotExistError] = []
    if not store.customer_exists(order.customer):
        error = CustomerDoesNotExistError()
        errors.append(error)
    return errors


def validate_application_exists(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[ApplicationNotValidError]:
    errors: list[ApplicationNotValidError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not store.get_application_by_tag(sample.application):
                error = ApplicationNotValidError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_application_not_archived(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[ApplicationArchivedError]:
    errors: list[ApplicationArchivedError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if store.is_application_archived(sample.application):
                error = ApplicationArchivedError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_gene_panels_unique(order: OrderWithCases, **kwargs) -> list[RepeatedGenePanelsError]:
    errors: list[RepeatedGenePanelsError] = []
    for case_index, case in order.enumerated_new_cases:
        if contains_duplicates(case.panels):
            error = RepeatedGenePanelsError(case_index=case_index)
            errors.append(error)
    return errors


def validate_gene_panels_exist(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[InvalidGenePanelsError]:
    errors: list[InvalidGenePanelsError] = []
    for case_index, case in order.enumerated_new_cases:
        if invalid_panels := get_invalid_panels(panels=case.panels, store=store):
            case_error = InvalidGenePanelsError(case_index=case_index, panels=invalid_panels)
            errors.append(case_error)
    return errors


def validate_volume_interval(order: OrderWithCases, **kwargs) -> list[InvalidVolumeError]:
    errors: list[InvalidVolumeError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_volume_invalid(sample):
                error = InvalidVolumeError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_case_names_available(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[CaseNameNotAvailableError]:
    errors: list[CaseNameNotAvailableError] = []
    customer = store.get_customer_by_internal_id(order.customer)
    for case_index, case in order.enumerated_new_cases:
        if store.get_case_by_name_and_customer(case_name=case.name, customer=customer):
            error = CaseNameNotAvailableError(case_index=case_index)
            errors.append(error)
    return errors


def validate_case_internal_ids_exist(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[CaseDoesNotExistError]:
    errors: list[CaseDoesNotExistError] = []
    for case_index, case in order.enumerated_existing_cases:
        case: Case | None = store.get_case_by_internal_id(case.internal_id)
        if not case:
            error = CaseDoesNotExistError(case_index=case_index)
            errors.append(error)
    return errors


def validate_samples_exist(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[SampleDoesNotExistError]:
    errors: list[SampleDoesNotExistError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_existing_samples:
            sample: Sample | None = store.get_sample_by_internal_id(sample.internal_id)
            if not sample:
                error = SampleDoesNotExistError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_sex_required_for_new_samples(order: OrderWithCases, **kwargs) -> list[SexMissingError]:
    errors: list[SexMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not sample.sex:
                error = SexMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_source_required(order: OrderWithCases, **kwargs) -> list[SourceMissingError]:
    errors: list[SourceMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not sample.source:
                error = SourceMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors
