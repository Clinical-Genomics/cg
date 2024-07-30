from typing import Callable

from pydantic import ValidationError

from cg.services.order_validation_service.models.errors import (
    CaseSampleError,
    OrderError,
    ValidationErrors,
)
from cg.services.order_validation_service.models.order import Order
from cg.store.store import Store


def apply_order_validation(rules: list[Callable], order: Order, store: Store) -> list[OrderError]:
    errors: list[OrderError] = []
    for rule in rules:
        rule_errors: list[OrderError] = rule(order=order, store=store)
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


def convert_errors(pydantic_errors: list[ValidationError]) -> ValidationErrors:
    pass
