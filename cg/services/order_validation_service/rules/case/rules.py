from cg.services.order_validation_service.errors.case_errors import (
    CaseDoesNotExistError,
    CaseNameNotAvailableError,
    DoubleNormalError,
    DoubleTumourError,
    MoreThanTwoSamplesInCaseError,
    MultipleSamplesInCaseError,
    NumberOfNormalSamplesError,
    RepeatedCaseNameError,
    RepeatedGenePanelsError,
)
from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.rules.case.utils import (
    contains_duplicates,
    is_double_normal,
    is_double_tumour,
)
from cg.services.order_validation_service.rules.case_sample.utils import (
    get_repeated_case_name_errors,
)
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.balsamic_umi.models.order import (
    BalsamicUmiOrder,
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


def validate_one_sample_per_case(
    order: OrderWithCases, **kwargs
) -> list[MultipleSamplesInCaseError]:
    """Validates that there is only one sample in each case.
    Only applicable to RNAFusion."""
    errors: list[MultipleSamplesInCaseError] = []
    for case_index, case in order.enumerated_new_cases:
        if len(case.samples) > 1:
            error = MultipleSamplesInCaseError(case_index=case_index)
            errors.append(error)
    return errors


def validate_at_most_two_samples_per_case(
    order: OrderWithCases, **kwargs
) -> list[MoreThanTwoSamplesInCaseError]:
    """Validates that there is at most two samples in each case.
    Only applicable to Balsamic and Balsamic-UMI."""
    errors: list[MoreThanTwoSamplesInCaseError] = []
    for case_index, case in order.enumerated_new_cases:
        if len(case.samples) > 2:
            error = MoreThanTwoSamplesInCaseError(case_index=case_index)
            errors.append(error)
    return errors


def validate_number_of_normal_samples(
    order: BalsamicOrder | BalsamicUmiOrder, store: Store, **kwargs
) -> list[NumberOfNormalSamplesError]:
    """Validates that Balsamic cases with pairs of samples contain one tumour and one normal sample.
    Only applicable to Balsamic and Balsamic-UMI."""
    errors: list[NumberOfNormalSamplesError] = []
    for case_index, case in order.enumerated_new_cases:
        if is_double_normal(case=case, store=store):
            error = DoubleNormalError(case_index=case_index)
            errors.append(error)
        elif is_double_tumour(case=case, store=store):
            error = DoubleTumourError(case_index=case_index)
            errors.append(error)
    return errors
