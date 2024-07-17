from typing import Callable

from cg.services.order_validation_service.models.errors import CaseSampleError, OrderError
from cg.services.order_validation_service.models.order import Order
from cg.store.store import Store


def apply_order_validation(rules: list[Callable], order: Order, store: Store) -> list[OrderError]:
    errors: list[OrderError] = []
    for rule in rules:
        rule_errors: list[OrderError] = rule(order=order, store=store)
        errors.extend(rule_errors)
    return errors


def apply_case_sample_validation(
    rules: list[Callable], case, store: Store
) -> list[CaseSampleError]:
    errors: list[CaseSampleError] = []
    for rule in rules:
        rule_errors: list[CaseSampleError] = rule(case=case, store=store)
        errors.extend(rule_errors)
    return errors
