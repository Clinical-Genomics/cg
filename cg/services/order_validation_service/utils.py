from typing import Callable

from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.validation_error import ValidationErrors
from cg.store.store import Store


def apply_validation(rules: list[Callable], order: Order, store: Store) -> ValidationErrors:

    errors = ValidationErrors()

    for rule in rules:
        rule_errors: ValidationErrors = rule(order=order, store=store)
        errors.errors.extend(rule_errors.errors)

    return errors
