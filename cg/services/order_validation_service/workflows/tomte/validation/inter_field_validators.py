from cg.services.order_validation_service.models.validation_error import (
    ValidationError,
    ValidationErrors,
)
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder


def each_case_contains_mother(order: TomteOrder) -> ValidationErrors:
    cases: list[TomteCase] = order.cases
    errors: list[ValidationError] = []
    for case in cases:
        has_mother: bool = case_has_mother(case)
        if not has_mother:
            error = ValidationError(
                message="All cases must contain a mother",
                field="unique_field_identifier_here",
            )
            errors.append(error)
    return ValidationErrors(errors)


def each_case_contains_father(order: TomteOrder) -> ValidationErrors:
    cases: list[TomteCase] = order.cases
    errors: list[ValidationError] = []
    for case in cases:
        has_father: bool = case_has_father(case)
        if not has_father:
            error = ValidationError(
                message="All cases must contain a father",
                field="unique_field_identifier_here",
            )
            errors.append(error)
    return ValidationErrors(errors)


def case_has_father(case: TomteCase) -> bool:
    return any(sample.father for sample in case.samples)


def case_has_mother(case: TomteCase) -> bool:
    return any(sample.mother for sample in case.samples)
