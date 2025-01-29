from pydantic_core import ErrorDetails, ValidationError

from cg.services.orders.validation.errors.case_errors import CaseError
from cg.services.orders.validation.errors.case_sample_errors import CaseSampleError
from cg.services.orders.validation.errors.order_errors import OrderError
from cg.services.orders.validation.errors.sample_errors import SampleError
from cg.services.orders.validation.errors.validation_errors import ValidationErrors


def convert_errors(pydantic_errors: ValidationError) -> ValidationErrors:
    error_details: list[ErrorDetails] = pydantic_errors.errors()
    order_errors: list[OrderError] = convert_order_errors(error_details)
    case_errors: list[CaseError] = convert_case_errors(error_details=error_details)
    case_sample_errors: list[CaseSampleError] = convert_case_sample_errors(
        error_details=error_details
    )
    sample_errors: list[SampleError] = convert_sample_errors(error_details=error_details)
    return ValidationErrors(
        order_errors=order_errors,
        case_errors=case_errors,
        case_sample_errors=case_sample_errors,
        sample_errors=sample_errors,
    )


def convert_order_errors(error_details: list[ErrorDetails]) -> list[OrderError]:
    errors: list[OrderError] = []
    order_details: list[ErrorDetails] = get_order_error_details(error_details)
    for error_detail in order_details:
        error: OrderError = create_order_error(error_detail)
        errors.append(error)
    return errors


def convert_case_errors(error_details: list[ErrorDetails]) -> list[CaseError]:
    errors: list[CaseError] = []
    case_details: list[ErrorDetails] = get_case_error_details(error_details)
    for error_detail in case_details:
        error: CaseError = create_case_error(error_detail)
        errors.append(error)
    return errors


def convert_sample_errors(error_details: list[ErrorDetails]) -> list[SampleError]:
    errors: list[SampleError] = []
    sample_details: list[ErrorDetails] = get_sample_error_details(error_details)
    for error_detail in sample_details:
        error: SampleError = create_sample_error(error_detail)
        errors.append(error)
    return errors


def create_order_error(error: ErrorDetails) -> OrderError:
    field_name: str = get_order_field_name(error)
    message: str = get_error_message(error)
    error = OrderError(field=field_name, message=message)
    return error


def create_sample_error(error: ErrorDetails) -> SampleError:
    sample_index: int = get_sample_index(error)
    field_name: str = get_sample_field_name(error)
    message: str = get_error_message(error)
    error = SampleError(sample_index=sample_index, field=field_name, message=message)
    return error


def create_case_error(error: ErrorDetails) -> CaseError:
    case_index: int = get_case_index(error=error)
    field_name: str = get_case_field_name(error)
    message: str = get_error_message(error)
    error = CaseError(case_index=case_index, field=field_name, message=message)
    return error


def convert_case_sample_errors(error_details: list[ErrorDetails]) -> list[CaseSampleError]:
    errors: list[CaseSampleError] = []
    case_sample_details: list[ErrorDetails] = get_case_sample_error_details(error_details)
    for error_detail in case_sample_details:
        error = create_case_sample_error(error_detail)
        errors.append(error)
    return errors


def create_case_sample_error(error: ErrorDetails) -> CaseSampleError:
    case_index: int = get_case_index(error=error)
    sample_index: int = get_case_sample_index(error=error)
    field_name: str = get_case_sample_field_name(error)
    message: str = get_error_message(error)
    error = CaseSampleError(
        case_index=case_index,
        sample_index=sample_index,
        field=field_name,
        message=message,
    )
    return error


"""
What follows below are ways of extracting data from a Pydantic ErrorDetails object. The aim is to find out
where the error occurred, for which the 'loc' value (which is a tuple) can be used. It is generally structured in 
alternating strings and ints, specifying field names and list indices. An example:
if loc = ('cases', 3, 'samples', 2, 'well_position'), that means that the error stems from the well_position of the
third sample in the fourth case.
"""


def get_sample_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_sample_error(error)]


def get_case_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_case_error(error)]


def get_case_sample_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_case_sample_error(error)]


def get_order_error_details(error_details: list[ErrorDetails]) -> list[ErrorDetails]:
    return [error for error in error_details if is_order_error(error)]


def is_sample_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 3 and error["loc"][0] == "samples"


def is_case_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 4 and error["loc"][0] == "cases"


def is_case_sample_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 7


def is_order_error(error: ErrorDetails) -> bool:
    return len(error["loc"]) == 1


def get_error_message(error: ErrorDetails) -> str:
    return error["msg"]


def get_sample_field_name(error: ErrorDetails) -> str:
    return error["loc"][2]


def get_case_field_name(error: ErrorDetails) -> str:
    return error["loc"][3]


def get_case_sample_field_name(error: ErrorDetails) -> str:
    return error["loc"][6]


def get_order_field_name(error: ErrorDetails) -> str:
    return error["loc"][0]


def get_sample_index(error: ErrorDetails) -> int:
    return error["loc"][1]


def get_case_index(error: ErrorDetails) -> int:
    return error["loc"][1]


def get_case_sample_index(error: ErrorDetails) -> int:
    return error["loc"][4]
