from typing import Any

from cg.services.orders.validation.errors.case_errors import CaseError
from cg.services.orders.validation.errors.case_sample_errors import CaseSampleError
from cg.services.orders.validation.errors.order_errors import OrderError
from cg.services.orders.validation.errors.sample_errors import SampleError
from cg.services.orders.validation.errors.validation_errors import ValidationErrors


def create_order_validation_response(raw_order: dict, errors: ValidationErrors) -> dict:
    """Ensures each field in the order looks like: {value: raw value, errors: [errors]}"""
    wrap_fields(raw_order)
    map_errors_to_order(order=raw_order, errors=errors)
    return raw_order


def map_errors_to_order(order: dict, errors: ValidationErrors) -> None:
    map_order_errors(order=order, errors=errors.order_errors)
    map_case_errors(order=order, errors=errors.case_errors)
    map_case_sample_errors(order=order, errors=errors.case_sample_errors)
    map_sample_errors(order=order, errors=errors.sample_errors)


def map_order_errors(order: dict, errors: list[OrderError]) -> None:
    for error in errors:
        add_error(entity=order, field=error.field, message=error.message)


def map_case_errors(order: dict, errors: list[CaseError]) -> None:
    for error in errors:
        case: dict = get_case(order=order, index=error.case_index)
        add_error(entity=case, field=error.field, message=error.message)


def map_case_sample_errors(order: dict, errors: list[CaseSampleError]) -> None:
    for error in errors:
        case: dict = get_case(order=order, index=error.case_index)
        sample: dict = get_case_sample(case=case, index=error.sample_index)
        add_error(entity=sample, field=error.field, message=error.message)


def map_sample_errors(order: dict, errors: list[SampleError]) -> None:
    for error in errors:
        sample: dict = get_sample(order=order, index=error.sample_index)
        add_error(entity=sample, field=error.field, message=error.message)


def add_error(entity: dict, field: str, message: str) -> None:
    if not entity.get(field):
        set_field(entity=entity, field=field, value=None)
    if field in {"sample_errors", "warnings"}:
        # Special handling since the 'value' corresponds to whether it is set
        entity[field]["value"] = True
    entity[field]["errors"].append(message)


def get_case(order: dict, index: int) -> dict:
    return order["cases"][index]


def get_case_sample(case: dict, index: int) -> dict:
    return case["samples"][index]


def get_sample(order: dict, index: int) -> dict:
    return order["samples"][index]


def wrap_fields(raw_order: dict) -> None:
    wrap_order_fields(raw_order)
    if raw_order.get("cases"):
        wrap_case_and_sample_fields(raw_order)
    else:
        wrap_sample_fields(raw_order["samples"])


def wrap_order_fields(raw_order: dict) -> None:
    for field, value in raw_order.items():
        if field not in {"cases", "samples"}:
            set_field(entity=raw_order, field=field, value=value)


def wrap_case_and_sample_fields(raw_order: dict) -> None:
    for case in raw_order["cases"]:
        wrap_case_fields(case)
        wrap_sample_fields(case["samples"])


def wrap_case_fields(case: dict) -> None:
    for field, value in case.items():
        if field != "samples":
            set_field(entity=case, field=field, value=value)
    set_field(entity=case, field="sample_errors", value=False)


def wrap_sample_fields(samples: list[dict]) -> None:
    for sample in samples:
        for field, value in sample.items():
            set_field(entity=sample, field=field, value=value)
        set_field(entity=sample, field="warnings", value=False)


def set_field(entity: dict, field: str, value: Any) -> None:
    entity[field] = {"value": value, "errors": []}
