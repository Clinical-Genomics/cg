from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.validation_error import ValidationErrors
from cg.services.order_validation_service.validators.inter_field_validators import (
    _create_order_error,
)
from cg.store.store import Store


def validate_user_belongs_to_customer(order: Order, store: Store) -> ValidationErrors | None:
    has_access: bool = store.user_belongs_to_customer(
        user_id=order.user_id,
        customer_internal_id=order.customer_internal_id,
    )

    if not has_access:
        return _create_user_not_in_customer_error()


def _create_user_not_in_customer_error() -> ValidationErrors:
    field = "customer"
    message = "User does not belong to customer"
    return _create_order_error(message=message, field=field)
