from cg.services.order_validation_service.errors.order_errors import (
    CustomerCannotSkipReceptionControlError,
    CustomerDoesNotExistError,
    OrderError,
    OrderNameRequiredError,
    TicketNumberRequiredError,
    UserNotAssociatedWithCustomerError,
)
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.rules.order.utils import (
    is_order_name_missing,
    is_ticket_number_missing,
)
from cg.store.store import Store


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


def validate_ticket_number_required_if_connected(
    order: Order,
    **kwargs,
) -> list[TicketNumberRequiredError]:
    errors: list[TicketNumberRequiredError] = []
    if is_ticket_number_missing(order):
        error = TicketNumberRequiredError()
        errors.append(error)
    return errors


def validate_name_required_for_new_order(order: Order, **kwargs) -> list[OrderNameRequiredError]:
    errors: list[OrderNameRequiredError] = []
    if is_order_name_missing(order):
        error = OrderNameRequiredError()
        errors.append(error)
    return errors


def validate_customer_can_skip_reception_control(
    order: Order,
    store: Store,
    **kwargs,
) -> list[CustomerCannotSkipReceptionControlError]:
    errors: list[CustomerCannotSkipReceptionControlError] = []

    if order.skip_reception_control and not store.is_customer_trusted(order.customer):
        error = CustomerCannotSkipReceptionControlError()
        errors.append(error)
    return errors