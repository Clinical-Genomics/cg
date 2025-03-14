from cg.services.orders.validation.errors.order_errors import (
    CustomerCannotSkipReceptionControlError,
    CustomerDoesNotExistError,
    UserNotAssociatedWithCustomerError,
)
from cg.services.orders.validation.models.order import Order
from cg.store.models import User
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


def validate_user_belongs_to_customer(
    order: Order, store: Store, **kwargs
) -> list[UserNotAssociatedWithCustomerError]:
    user: User = store.get_user_by_entry_id(order._user_id)
    has_access: bool = store.is_user_associated_with_customer(
        user_id=order._user_id,
        customer_internal_id=order.customer,
    )
    errors: list[UserNotAssociatedWithCustomerError] = []
    if not (user.is_admin or has_access):
        error = UserNotAssociatedWithCustomerError()
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
