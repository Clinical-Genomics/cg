from typing import Callable

from cg.models.orders.sample_base import ControlEnum
from cg.services.orders.validation.constants import ElutionBuffer, ExtractionMethod
from cg.services.orders.validation.errors.case_errors import CaseError
from cg.services.orders.validation.errors.case_sample_errors import CaseSampleError
from cg.services.orders.validation.errors.order_errors import OrderError
from cg.services.orders.validation.errors.sample_errors import SampleError
from cg.services.orders.validation.models.order import Order
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


def parse_buffer(buffer: str | None) -> ElutionBuffer | None:
    return ElutionBuffer.OTHER if buffer and buffer.startswith("Other") else buffer


def parse_control(control: ControlEnum | None) -> ControlEnum:
    """Convert the control value into one of the Enum values if it's None."""
    return control or ControlEnum.not_control


def parse_extraction_method(extraction_method: str | None) -> ExtractionMethod:
    return (
        ExtractionMethod.MAGNAPURE_96
        if extraction_method and extraction_method.startswith(ExtractionMethod.MAGNAPURE_96)
        else extraction_method
    )
