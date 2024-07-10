from typing import Callable

from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.models.validation_error import ValidationErrors


def apply_validation(rules: list[Callable], order: Order) -> ValidationErrors:

    errors = ValidationErrors()

    for rule in rules:
        rule_errors: ValidationErrors = rule(order)
        errors.errors.extend(rule_errors.errors)

    return errors
