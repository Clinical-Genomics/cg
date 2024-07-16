from typing import Callable

from cg.services.order_validation_service.models.errors import CaseSampleError, ValidationError
from cg.services.order_validation_service.models.order import Order
from cg.store.store import Store


def apply_order_validation(rules: list[Callable], order: Order, store: Store) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for rule in rules:
        rule_errors: list[ValidationError] = rule(order=order, store=store)
        errors.extend(rule_errors)
    return errors


def apply_case_sample_validation(rules: list[Callable], case, store: Store) -> list[CaseSampleError]:
    errors: list[ValidationError] = []
    for rule in rules:
        rule_errors: list[ValidationError] = rule(case=case, store=store)
        errors.extend(rule_errors)
    return errors
