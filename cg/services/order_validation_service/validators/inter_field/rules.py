from cg.constants import PrepCategory, Workflow
from cg.services.order_validation_service.constants import (
    ALLOWED_SKIP_RC_BUFFERS,
    WORKFLOW_PREP_CATEGORIES,
)
from cg.services.order_validation_service.models.errors import (
    ApplicationNotCompatibleError,
    ConcentrationRequiredIfSkipRCError,
    ContainerNameMissingError,
    InvalidBufferError,
    OrderNameRequiredError,
    SubjectIdSameAsSampleNameError,
    TicketNumberRequiredError,
    WellPositionMissingError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.validators.inter_field.utils import (
    _is_application_not_compatible,
    _is_order_name_missing,
    _is_ticket_number_missing,
    is_concentration_missing,
    is_container_name_missing,
    is_well_position_missing,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.store.store import Store


def validate_ticket_number_required_if_connected(
    order: Order, **kwargs
) -> list[TicketNumberRequiredError]:
    errors: list[TicketNumberRequiredError] = []
    if _is_ticket_number_missing(order):
        error = TicketNumberRequiredError()
        errors.append(error)
    return errors


def validate_name_required_for_new_order(order: Order, **kwargs) -> list[OrderNameRequiredError]:
    errors: list[OrderNameRequiredError] = []
    if _is_order_name_missing(order):
        error = OrderNameRequiredError()
        errors.append(error)
    return errors


def validate_application_compatibility(
    order: TomteOrder, store: Store, **kwargs
) -> list[ApplicationNotCompatibleError]:
    errors: list[ApplicationNotCompatibleError] = []
    workflow: Workflow = order.workflow
    allowed_prep_categories: list[PrepCategory] = WORKFLOW_PREP_CATEGORIES[workflow]
    for case_index, case in order.enumerated_cases:
        for sample_index, sample in case.enumerated_samples:
            if _is_application_not_compatible(
                allowed_prep_categories=allowed_prep_categories,
                application_tag=sample.application,
                store=store,
            ):
                error = ApplicationNotCompatibleError(
                    case_index=case_index, sample_index=sample_index
                )
                errors.append(error)
    return errors


def validate_buffer_skip_rc_condition(order: TomteOrder) -> list[InvalidBufferError]:
    errors: list[InvalidBufferError] = []
    if order.skip_reception_control:
        errors.extend(validate_buffers_are_allowed(order))
    return errors


def validate_buffers_are_allowed(order: TomteOrder) -> list[InvalidBufferError]:
    errors = []
    for case_index, case in order.enumerated_cases:
        for sample_index, sample in case.enumerated_samples:
            if sample.elution_buffer not in ALLOWED_SKIP_RC_BUFFERS:
                error = InvalidBufferError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_concentration_required_if_skip_rc(
    order: TomteOrder,
) -> list[ConcentrationRequiredIfSkipRCError]:
    if not order.skip_reception_control:
        return []
    errors: list[ConcentrationRequiredIfSkipRCError] = []
    for case_index, case in order.enumerated_cases:
        for sample_index, sample in case.enumerated_samples:
            if is_concentration_missing(sample):
                error = ConcentrationRequiredIfSkipRCError(
                    case_index=case_index, sample_index=sample_index
                )
                errors.append(error)
    return errors


def validate_subject_ids_different_from_sample_names(
    order: TomteOrder,
) -> list[SubjectIdSameAsSampleNameError]:
    errors: list[SubjectIdSameAsSampleNameError] = []
    for case_index, case in order.enumerated_cases:
        for sample_index, sample in case.enumerated_samples:
            if sample.name == sample.subject_id:
                error = SubjectIdSameAsSampleNameError(
                    case_index=case_index, sample_index=sample_index
                )
                errors.append(error)
    return errors


def validate_well_positions_required(order: TomteOrder) -> list[WellPositionMissingError]:
    errors: list[WellPositionMissingError] = []
    for case_index, case in order.enumerated_cases:
        for sample_index, sample in case.enumerated_samples:
            if is_well_position_missing(sample):
                error = WellPositionMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_container_name_required(order: TomteOrder) -> list[ContainerNameMissingError]:
    errors: list[ContainerNameMissingError] = []
    for case_index, case in order.enumerated_cases:
        for sample_index, sample in case.enumerated_samples:
            if is_container_name_missing(sample):
                error = ContainerNameMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors
