from pydantic_core import ErrorDetails, ValidationError
from cg.services.order_validation_service.models.errors import (
    CaseError,
    CaseSampleError,
    OrderError,
    SampleError,
    ValidationErrors,
)


def convert_errors(pydantic_errors: ValidationError, order: dict) -> ValidationErrors:
    error_details: list[ErrorDetails] = pydantic_errors.errors()
    order_errors = convert_order_errors(error_details)
    case_errors = convert_case_errors(error_details=error_details, order=order)
    case_sample_errors = convert_case_sample_errors(error_details=error_details, order=order)
    sample_errors = convert_sample_errors(error_details=error_details, order=order)
    return ValidationErrors(
        order_errors=order_errors,
        case_errors=case_errors,
        case_sample_errors=case_sample_errors,
        sample_errors=sample_errors,
    )


def convert_sample_errors(error_details: list[ErrorDetails], order: dict) -> list[SampleError]:
    errors: list[SampleError] = []
    sample_details = get_sample_error_details(error_details)
    for error in sample_details:
        sample_name = order["samples"][error["loc"][1]]["name"]
        field_name = error["loc"][2]
        message = error["msg"]
        error = SampleError(sample_name=sample_name, field=field_name, message=message)
        errors.append(error)
    return errors


def get_sample_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_sample_error(error)]


def is_sample_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 3 and error["loc"][0] == "samples"


def convert_order_errors(error_details: list[ErrorDetails]) -> list[OrderError]:
    errors: list[OrderError] = []
    order_details = get_order_error_details(error_details)
    for error in order_details:
        field_name = error["loc"][0]
        message = error["msg"]
        error = OrderError(field=field_name, message=message)
        errors.append(error)
    return errors


def convert_case_errors(error_details: list[ErrorDetails], order: dict) -> list[CaseError]:
    errors: list[CaseError] = []
    case_details = get_case_error_details(error_details)
    for error in case_details:
        case_name = order["cases"][error["loc"][1]]["name"]
        field_name = error["loc"][2]
        message = error["msg"]
        error = CaseError(case_name=case_name, field=field_name, message=message)
        errors.append(error)
    return errors


def convert_case_sample_errors(
    error_details: list[ErrorDetails], order: dict
) -> list[CaseSampleError]:
    errors: list[CaseSampleError] = []
    case_sample_details = get_case_sample_error_details(error_details)
    for error in case_sample_details:
        case_name = order["cases"][error["loc"][1]]["name"]
        sample_name = order["cases"][error["loc"][1]]["samples"][error["loc"][3]]["name"]
        field_name = error["loc"][4]
        message = error["msg"]
        error = CaseSampleError(
            case_name=case_name, sample_name=sample_name, field_name=field_name, message=message
        )
        errors.append(error)
    return errors


def get_case_sample_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_case_sample_error(error)]


def is_case_sample_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 5


def get_case_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_case_error(error)]


def get_order_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_order_error(error)]


def is_case_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 3 and error["loc"][0] == "cases"


def is_order_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 1
