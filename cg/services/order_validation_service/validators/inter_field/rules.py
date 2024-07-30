from cg.constants import PrepCategory, Workflow
from cg.services.order_validation_service.constants import WORKFLOW_PREP_CATEGORIES
from cg.services.order_validation_service.models.errors import (
    ApplicationNotCompatibleError,
    OrderError,
    OrderNameRequiredError,
    TicketNumberRequiredError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.inter_field.utils import (
    _is_application_compatible,
    _is_order_name_required,
    _is_ticket_number_missing,
)
from cg.store.store import Store


def validate_ticket_number_required_if_connected(order: Order, **kwargs) -> list[OrderError]:
    errors: list[OrderError] = []
    if _is_ticket_number_missing(order):
        error = TicketNumberRequiredError()
        errors.append(error)
    return errors


def validate_name_required_for_new_order(order: Order, **kwargs) -> list[OrderError]:
    errors: list[OrderError] = []
    if _is_order_name_required(order):
        error = OrderNameRequiredError()
        errors.append(error)
    return errors


def validate_application_compatibility(
    order: Order, store: Store, **kwargs
) -> list[ApplicationNotCompatibleError]:
    errors: list[ApplicationNotCompatibleError] = []
    workflow: Workflow = order.workflow
    allowed_prep_categories: list[PrepCategory] = WORKFLOW_PREP_CATEGORIES[workflow]
    for case in order.cases:
        for sample in case.samples:
            if not _is_application_compatible(
                allowed_prep_categories=allowed_prep_categories,
                application_tag=sample.application,
                store=store,
            ):
                error = ApplicationNotCompatibleError(case_name=case.name, sample_name=sample.name)
                errors.append(error)
    return errors
