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
        add_error_to_order(order=order, error=error)


def map_case_errors(order: dict, errors: list[CaseError]) -> None:
    for error in errors:
        case: dict = get_case(order=order, index=error.case_index)
        add_error_to_case(case=case, error=error)


def map_case_sample_errors(order: dict, errors: list[CaseSampleError]) -> None:
    for error in errors:
        case: dict = get_case(order=order, index=error.case_index)
        sample: dict = get_sample(case=case, index=error.sample_index)
        add_error_to_sample_field(sample=sample, error=error)


def add_error_to_order(order: dict, error: OrderError) -> None:
    order[error.field]["errors"].append(error.message)


def add_error_to_case(case: dict, error: CaseError) -> None:
    case[error.field]["errors"].append(error.message)


def get_case(order: dict, index: int) -> dict:
    return order["cases"][index]


def get_sample(case: dict, index: int) -> dict:
    return case["samples"][index]


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
