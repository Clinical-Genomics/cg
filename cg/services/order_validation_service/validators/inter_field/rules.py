from cg.constants import PrepCategory, Workflow
from cg.services.order_validation_service.constants import WORKFLOW_PREP_CATEGORIES
from cg.services.order_validation_service.models.errors import (
    ApplicationNotCompatibleError,
    CaseSampleError,
    InvalidBufferError,
    OrderError,
    OrderNameRequiredError,
    TicketNumberRequiredError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.inter_field.utils import (
    _is_application_not_compatible,
    _is_order_name_required,
    _is_ticket_number_missing,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
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
    order: TomteOrder, store: Store, **kwargs
) -> list[ApplicationNotCompatibleError]:
    errors: list[ApplicationNotCompatibleError] = []
    workflow: Workflow = order.workflow
    allowed_prep_categories: list[PrepCategory] = WORKFLOW_PREP_CATEGORIES[workflow]
    for case in order.cases:
        for sample in case.samples:
            if _is_application_not_compatible(
                allowed_prep_categories=allowed_prep_categories,
                application_tag=sample.application,
                store=store,
            ):
                error = ApplicationNotCompatibleError(case_name=case.name, sample_name=sample.name)
                errors.append(error)
    return errors


def validate_skip_rc_buffer_condition(order: TomteOrder) -> list[CaseSampleError]:
    errors: list[CaseSampleError] = []

    if order.skip_reception_control:
        validate_buffers_are_allowed(order)
    return errors


def validate_buffers_are_allowed(order: Order) -> list[CaseSampleError]:
    errors = []
    allowed_buffers = ["Nuclease-free water", "Tris-HCl"]
    for case in order.cases:
        for sample in case.samples:
            if sample.elution_buffer not in allowed_buffers:
                error = InvalidBufferError(case_name=case.name, sample_name=sample.name)
                errors.append(error)
    return errors
