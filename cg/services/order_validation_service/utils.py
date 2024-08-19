from typing import Callable

from cg.services.order_validation_service.models.errors import (
    CaseError,
    CaseSampleError,
    OrderError,
    SampleError,
)
from cg.services.order_validation_service.models.order import Order
from cg.store.store import Store


def apply_order_validation(rules: list[Callable], order: Order, store: Store) -> list[OrderError]:
    errors: list[OrderError] = []
    for rule in rules:
        rule_errors: list[OrderError] = rule(order=order, store=store)
        errors.extend(rule_errors)
    return errors


def apply_case_validation(rules: list[Callable], order: Order, store: Store) -> list[CaseError]:
    errors: list[CaseError] = []
    for rule in rules:
        rule_errors: list[CaseError] = rule(order=order, store=store)
        errors.extend(rule_errors)
    return errors


def apply_case_sample_validation(
    rules: list[Callable], order: Order, store: Store
) -> list[CaseSampleError]:
    errors: list[CaseSampleError] = []
    for rule in rules:
        rule_errors: list[CaseSampleError] = rule(order=order, store=store)
        errors.extend(rule_errors)
    return errors


def apply_sample_validation(rules: list[Callable], order: Order, store: Store) -> list[SampleError]:
    errors: list[SampleError] = []
    for rule in rules:
        rule_errors: list[SampleError] = rule(order=order, store=store)
        errors.extend(rule_errors)
    return errors
