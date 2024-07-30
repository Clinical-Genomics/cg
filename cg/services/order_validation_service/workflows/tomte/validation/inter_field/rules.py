from cg.constants.subject import Sex
from cg.services.order_validation_service.models.errors import (
    InvalidFatherSexError,
    OccupiedWellError,
    RepeatedCaseNameError,
    RepeatedSampleNameError,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.utils import (
    _get_errors,
    _get_excess_samples,
    _get_plate_samples,
    get_father_sex_errors,
    get_repeated_case_name_errors,
    get_repeated_sample_name_errors,
)


def validate_wells_contain_at_most_one_sample(order: TomteOrder) -> list[OccupiedWellError]:
    samples_with_cases = _get_plate_samples(order)
    samples = _get_excess_samples(samples_with_cases)
    return _get_errors(samples)


def validate_no_repeated_case_names(order: TomteOrder) -> list[RepeatedCaseNameError]:
    return get_repeated_case_name_errors(order)


def validate_no_repeated_sample_names(order: TomteOrder) -> list[RepeatedSampleNameError]:
    errors: list[RepeatedSampleNameError] = []
    for case in order.cases:
        case_errors = get_repeated_sample_name_errors(case)
        errors.extend(case_errors)
    return errors


def validate_fathers_are_male(order: TomteOrder) -> list[InvalidFatherSexError]:
    errors: list[InvalidFatherSexError] = []
    for case in order.cases:
        case_errors = get_father_sex_errors(case)
        errors.extend(case_errors)
    return errors
