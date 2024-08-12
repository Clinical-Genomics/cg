from pydantic_core import ErrorDetails, ValidationError

from cg.services.order_validation_service.models.errors import (
    CaseError,
    CaseSampleError,
    OrderError,
    SampleError,
    ValidationErrors,
)


def convert_errors(pydantic_errors: ValidationError) -> ValidationErrors:
    error_details: list[ErrorDetails] = pydantic_errors.errors()
    order_errors = convert_order_errors(error_details)
    case_errors = convert_case_errors(error_details=error_details)
    case_sample_errors = convert_case_sample_errors(error_details=error_details)
    sample_errors = convert_sample_errors(error_details=error_details)
    return ValidationErrors(
        order_errors=order_errors,
        case_errors=case_errors,
        case_sample_errors=case_sample_errors,
        sample_errors=sample_errors,
    )


def convert_order_errors(error_details: list[ErrorDetails]) -> list[OrderError]:
    errors: list[OrderError] = []
    order_details = get_order_error_details(error_details)
    for error in order_details:
        error = create_order_error(error)
        errors.append(error)
    return errors


def convert_case_errors(error_details: list[ErrorDetails]) -> list[CaseError]:
    errors: list[CaseError] = []
    case_details = get_case_error_details(error_details)
    for error in case_details:
        error = create_case_error(error)
        errors.append(error)
    return errors


def convert_sample_errors(error_details: list[ErrorDetails]) -> list[SampleError]:
    errors: list[SampleError] = []
    sample_details = get_sample_error_details(error_details)
    for error in sample_details:
        error = create_sample_error(error)
        errors.append(error)
    return errors


def create_order_error(error: ErrorDetails) -> OrderError:
    field_name = get_order_field_name(error)
    message = get_error_message(error)
    error = OrderError(field=field_name, message=message)
    return error


def create_sample_error(error: ErrorDetails) -> SampleError:
    sample_index = get_sample_index(error=error)
    field_name = get_sample_field_name(error)
    message = get_error_message(error)
    error = SampleError(sample_index=sample_index, field=field_name, message=message)
    return error


def create_case_error(error: ErrorDetails) -> CaseError:
    case_index = get_case_index(error=error)
    field_name = get_case_field_name(error)
    message = get_error_message(error)
    error = CaseError(case_index=case_index, field=field_name, message=message)
    return error


def convert_case_sample_errors(error_details: list[ErrorDetails]) -> list[CaseSampleError]:
    errors: list[CaseSampleError] = []
    case_sample_details = get_case_sample_error_details(error_details)
    for error in case_sample_details:
        error = create_case_sample_error(error=error)
        errors.append(error)
    return errors


def create_case_sample_error(error: ErrorDetails) -> CaseSampleError:
    case_index = get_case_index(error=error)
    sample_index = get_case_sample_index(error=error)
    field_name = get_case_sample_field_name(error)
    message = get_error_message(error)
    error = CaseSampleError(
        case_index=case_index,
        sample_index=sample_index,
        field=field_name,
        message=message,
    )
    return error


def is_sample_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 3 and error["loc"][0] == "samples"


def is_case_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 3 and error["loc"][0] == "cases"


def is_case_sample_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 5


def is_order_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 1


def get_sample_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_sample_error(error)]


def get_case_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_case_error(error)]


def get_case_sample_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_case_sample_error(error)]


def get_order_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_order_error(error)]


def get_error_message(error: ErrorDetails) -> str:
    return error["msg"]


def get_sample_field_name(error: ErrorDetails) -> str:
    return error["loc"][2]


def get_case_field_name(error: ErrorDetails) -> str:
    return error["loc"][2]


def get_case_sample_field_name(error: ErrorDetails) -> str:
    return error["loc"][4]


def get_order_field_name(error: ErrorDetails) -> str:
    return error["loc"][0]


def get_sample_index(error: ErrorDetails) -> int:
    return error["loc"][1]


def get_case_index(error: ErrorDetails) -> int:
    return error["loc"][1]


def get_case_sample_index(error: ErrorDetails) -> int:
    return error["loc"][3]
