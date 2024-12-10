from cg.constants import GenePanelMasterList
from cg.services.order_validation_service.errors.case_errors import (
    CaseDoesNotExistError,
    CaseNameNotAvailableError,
    RepeatedCaseNameError,
)
from cg.services.order_validation_service.models.existing_case import ExistingCase
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.rules.case.rules import (
    validate_case_internal_ids_exist,
    validate_case_names_available,
    validate_case_names_not_repeated,
)
from cg.store.models import Case
from cg.store.store import Store


def test_case_name_not_available(
    valid_order: OrderWithCases, store_with_multiple_cases_and_samples: Store
):
    store = store_with_multiple_cases_and_samples

    # GIVEN an order with a new case that has the same name as an existing case
    case: Case = store.get_cases()[0]
    valid_order.cases[0].name = case.name
    valid_order.customer = case.customer.internal_id

    # WHEN validating that the case name is available
    errors: list[CaseNameNotAvailableError] = validate_case_names_available(
        order=valid_order, store=store
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the case name
    assert isinstance(errors[0], CaseNameNotAvailableError)


def test_case_internal_ids_does_not_exist(
    valid_order: OrderWithCases,
    store_with_multiple_cases_and_samples: Store,
):

    # GIVEN an order with a case marked as existing but which does not exist in the database
    existing_case = ExistingCase(internal_id="Non-existent case", panels=[GenePanelMasterList.AID])
    valid_order.cases.append(existing_case)

    # WHEN validating that the internal ids match existing cases
    errors: list[CaseDoesNotExistError] = validate_case_internal_ids_exist(
        order=valid_order,
        store=store_with_multiple_cases_and_samples,
    )

    # THEN an error should be returned
    assert errors

    # THEN the error should concern the non-existent case
    assert isinstance(errors[0], CaseDoesNotExistError)


def test_repeated_case_names_not_allowed(order_with_repeated_case_names: OrderWithCases):
    # GIVEN an order with cases with the same name

    # WHEN validating the order
    errors: list[RepeatedCaseNameError] = validate_case_names_not_repeated(
        order_with_repeated_case_names
    )

    # THEN errors are returned
    assert errors

    # THEN the errors are about the case names
    assert isinstance(errors[0], RepeatedCaseNameError)
