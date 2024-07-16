from typing import Callable

from cg.services.order_validation_service.models.errors import OrderValidationError
from cg.services.order_validation_service.models.order import Order
from cg.store.store import Store


def apply_validation(rules: list[Callable], order: Order, store: Store) -> list[OrderValidationError]:
    errors: list[OrderValidationError] = []
    for rule in rules:
        rule_errors: list[OrderValidationError] = rule(order=order, store=store)
        errors.extend(rule_errors)
    return errors
