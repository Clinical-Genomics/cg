from cg.services.order_validation_service.models.errors import (
    CaseError,
    CaseSampleError,
    OrderError,
    ValidationErrors,
)


def create_validated_order_response(raw_order: dict, errors: ValidationErrors) -> dict:
    wrap_fields(raw_order)
    map_errors_to_order(raw_order, errors)
    return raw_order


def map_errors_to_order(order: dict, errors: ValidationErrors) -> None:
    map_order_errors(order=order, errors=errors.order_errors)
    map_case_errors(order=order, errors=errors.case_errors)
    map_case_sample_errors(order=order, errors=errors.case_sample_errors)


def map_order_errors(order: dict, errors: list[OrderError]) -> None:
    for error in errors:
        order[error.field]["errors"].append(error.message)


def map_case_errors(order: dict, errors: list[CaseError]) -> None:
    for error in errors:
        order["cases"][error.case_index][error.field]["errors"].append(error.message)


def map_case_sample_errors(order: dict, errors: list[CaseSampleError]) -> None:
    for error in errors:
        case: dict = get_case(order, error.case_index)
        sample: dict = get_sample(case, error.sample_index)
        add_error_to_sample_field(sample, error)


def get_case(order: dict, case_index: int) -> dict:
    return order["cases"][case_index]


def get_sample(case: dict, sample_index: int) -> dict:
    return case["samples"][sample_index]


def add_error_to_sample_field(sample: dict, error: CaseSampleError) -> None:
    sample[error.field]["errors"].append(error.message)


def wrap_fields(raw_order: dict) -> None:
    wrap_order_fields(raw_order)
    wrap_case_and_sample_fields(raw_order)


def wrap_order_fields(raw_order: dict) -> None:
    for field, value in raw_order.items():
        if field not in {"cases", "samples"}:
            raw_order[field] = {"value": value, "errors": []}


def wrap_case_and_sample_fields(raw_order: dict) -> None:
    for case in raw_order["cases"]:
        wrap_case_fields(case)
        wrap_sample_fields(case["samples"])


def wrap_case_fields(case: dict) -> None:
    for field, value in case.items():
        if field != "samples":
            case[field] = {"value": value, "errors": []}


def wrap_sample_fields(samples: list[dict]) -> None:
    for sample in samples:
        for field, value in sample.items():
            sample[field] = {"value": value, "errors": []}
