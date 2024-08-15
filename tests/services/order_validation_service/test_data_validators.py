from cg.services.order_validation_service.models.errors import (
    ApplicationArchivedError,
    ApplicationNotValidError,
    CaseNameNotAvailableError,
    InvalidGenePanelsError,
    RepeatedGenePanelsError,
)
from cg.services.order_validation_service.validators.data.rules import (
    validate_application_exists,
    validate_application_not_archived,
    validate_case_names_available,
    validate_gene_panels_exist,
    validate_gene_panels_unique,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.store.models import Application
from cg.store.store import Store


def test_applications_exist(valid_order: TomteOrder, base_store: Store):
    # GIVEN an order where one of the samples has an invalid application
    for case in valid_order.cases:
        case.samples[0].application = "Invalid application"

    # WHEN validating the order
    errors = validate_application_exists(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the ticket number
    assert isinstance(errors[0], ApplicationNotValidError)


def test_applications_not_archived(
    valid_order: TomteOrder, base_store: Store, archived_application: Application
):
    # GIVEN an order where one of the samples has an invalid application
    base_store.session.add(archived_application)
    base_store.commit_to_store()
    for case in valid_order.cases:
        case.samples[0].application = archived_application.tag

    # WHEN validating the order
    errors = validate_application_not_archived(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should be about the ticket number
    assert isinstance(errors[0], ApplicationArchivedError)


def test_invalid_gene_panels(valid_order: TomteOrder, base_store: Store):
    # GIVEN an order with an invalid gene panel specified
    invalid_panel = "Non-existent panel"
    valid_order.cases[0].panels = [invalid_panel]

    # WHEN validating that the gene panels exist
    errors = validate_gene_panels_exist(order=valid_order, store=base_store)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern invalid gene panels
    assert isinstance(errors[0], InvalidGenePanelsError)


def test_repeated_gene_panels(valid_order: TomteOrder, store_with_panels: Store):

    # GIVEN an order with repeated gene panels specified
    panel = store_with_panels.get_panels()[0].abbrev
    valid_order.cases[0].panels = [panel, panel]

    # WHEN validating that the gene panels are unique
    errors = validate_gene_panels_unique(order=valid_order)

    # THEN an error should be returned
    assert errors

    # THEN the error should concern repeated gene panels
    assert isinstance(errors[0], RepeatedGenePanelsError)


def test_case_name_not_available(valid_order: TomteOrder, store_with_multiple_cases_and_samples: Store):
    store = store_with_multiple_cases_and_samples
    
    # GIVEN an order with a new case that has the same name as an existing case
    case = store.get_cases()[0]
    valid_order.cases[0].name = case.name
    valid_order.customer_internal_id = case.customer.internal_id
    
    # WHEN validating that the case name is available
    errors = validate_case_names_available(order=valid_order, store=store)

    # THEN an error should be returned
    assert errors
    
    # THEN the error should concern the case name
    assert isinstance(errors[0], CaseNameNotAvailableError)
