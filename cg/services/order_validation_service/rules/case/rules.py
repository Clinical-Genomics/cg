from cg.services.order_validation_service.errors.case_errors import (
    CaseDoesNotExistError,
    CaseNameNotAvailableError,
    MultipleSamplesError,
    RepeatedCaseNameError,
    RepeatedGenePanelsError,
)
from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.rules.case.utils import contains_duplicates
from cg.services.order_validation_service.rules.case_sample.utils import (
    get_repeated_case_name_errors,
)
from cg.store.store import Store


def validate_gene_panels_unique(order: OrderWithCases, **kwargs) -> list[RepeatedGenePanelsError]:
    errors: list[RepeatedGenePanelsError] = []
    for case_index, case in order.enumerated_new_cases:
        if contains_duplicates(case.panels):
            error = RepeatedGenePanelsError(case_index=case_index)
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


def validate_case_names_not_repeated(
    order: OrderWithCases,
    **kwargs,
) -> list[RepeatedCaseNameError]:
    return get_repeated_case_name_errors(order)


def validate_one_sample_per_case(order: OrderWithCases, **kwargs) -> list[MultipleSamplesError]:
    errors: list[MultipleSamplesError] = []
    for case_index, case in order.enumerated_new_cases:
        if len(case.samples) > 1:
            error = MultipleSamplesError(case_index=case_index)
            errors.append(error)
    return errors
