from cg.services.order_validation_service.errors.case_errors import (
    RepeatedCaseNameError,
)
from cg.services.order_validation_service.errors.case_sample_errors import (
    FatherNotInCaseError,
    InvalidConcentrationIfSkipRCError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    MotherNotInCaseError,
    OccupiedWellError,
    PedigreeError,
    SampleNameRepeatedError,
    StatusMissingError,
    SubjectIdSameAsCaseNameError,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.rules.case_sample.pedigree.validate_pedigree import get_pedigree_errors
from cg.services.order_validation_service.workflows.tomte.rules.case_sample.utils import (
    get_father_case_errors,
    get_father_sex_errors,
    get_mother_case_errors,
    get_mother_sex_errors,
    get_occupied_well_errors,
    get_repeated_case_name_errors,
    get_repeated_sample_name_errors,
    get_well_sample_map,
    validate_concentration_in_case,
    validate_subject_ids_in_case,
)
from cg.store.store import Store


def validate_wells_contain_at_most_one_sample(
    order: TomteOrder, **kwargs
) -> list[OccupiedWellError]:
    errors: list[OccupiedWellError] = []
    well_position_to_sample_map: dict[tuple[str, str], list[tuple[int, int]]] = get_well_sample_map(
        order
    )
    for indices in well_position_to_sample_map.values():
        if len(indices) > 1:
            well_errors = get_occupied_well_errors(indices[1:])
            errors.extend(well_errors)
    return errors


def validate_case_names_not_repeated(order: TomteOrder, **kwargs) -> list[RepeatedCaseNameError]:
    return get_repeated_case_name_errors(order)


def validate_sample_names_not_repeated(
    order: TomteOrder, **kwargs
) -> list[SampleNameRepeatedError]:
    errors: list[SampleNameRepeatedError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[SampleNameRepeatedError] = get_repeated_sample_name_errors(
            case=case, case_index=index
        )
        errors.extend(case_errors)
    return errors


def validate_fathers_are_male(order: TomteOrder, **kwargs) -> list[InvalidFatherSexError]:
    errors: list[InvalidFatherSexError] = []
    for index, case in order.enumerated_cases:
        case_errors: list[InvalidFatherSexError] = get_father_sex_errors(
            case=case, case_index=index
        )
        errors.extend(case_errors)
    return errors


def validate_fathers_in_same_case_as_children(
    order: TomteOrder, **kwargs
) -> list[FatherNotInCaseError]:
    errors: list[FatherNotInCaseError] = []
    for index, case in order.enumerated_cases:
        case_errors: list[FatherNotInCaseError] = get_father_case_errors(
            case=case,
            case_index=index,
        )
        errors.extend(case_errors)
    return errors


def validate_mothers_are_female(order: TomteOrder, **kwargs) -> list[InvalidMotherSexError]:
    errors: list[InvalidMotherSexError] = []
    for index, case in order.enumerated_cases:
        case_errors: list[InvalidMotherSexError] = get_mother_sex_errors(
            case=case,
            case_index=index,
        )
        errors.extend(case_errors)
    return errors


def validate_mothers_in_same_case_as_children(
    order: TomteOrder, **kwargs
) -> list[MotherNotInCaseError]:
    errors: list[MotherNotInCaseError] = []
    for index, case in order.enumerated_cases:
        case_errors: list[MotherNotInCaseError] = get_mother_case_errors(
            case=case, case_index=index
        )
        errors.extend(case_errors)
    return errors


def validate_pedigree(order: TomteOrder, **kwargs) -> list[PedigreeError]:
    errors: list[PedigreeError] = []
    for case_index, case in order.enumerated_cases:
        case_errors: list[PedigreeError] = get_pedigree_errors(case=case, case_index=case_index)
        errors.extend(case_errors)
    return errors


def validate_subject_ids_different_from_case_names(
    order: TomteOrder, **kwargs
) -> list[SubjectIdSameAsCaseNameError]:
    errors: list[SubjectIdSameAsCaseNameError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[SubjectIdSameAsCaseNameError] = validate_subject_ids_in_case(
            case=case, case_index=index
        )
        errors.extend(case_errors)
    return errors


def validate_concentration_interval_if_skip_rc(
    order: TomteOrder, store: Store, **kwargs
) -> list[InvalidConcentrationIfSkipRCError]:
    if not order.skip_reception_control:
        return []
    errors: list[InvalidConcentrationIfSkipRCError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[InvalidConcentrationIfSkipRCError] = validate_concentration_in_case(
            case=case, case_index=index, store=store
        )
        errors.extend(case_errors)
    return errors


def validate_status_required_if_new(order: TomteOrder, **kwargs) -> list[StatusMissingError]:
    errors: list[StatusMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not sample.status:
                error = StatusMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors
