from cg.services.order_validation_service.models.errors import (
    FatherNotInCaseError,
    InvalidConcentrationIfSkipRCError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    MotherNotInCaseError,
    OccupiedWellError,
    PedigreeError,
    RepeatedCaseNameError,
    RepeatedSampleNameError,
    SubjectIdSameAsCaseNameError,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.pedigree.validate_pedigree import (
    get_pedigree_errors,
)
from cg.services.order_validation_service.workflows.tomte.validation.inter_field.utils import (
    _is_sample_on_plate,
    get_father_case_errors,
    get_father_sex_errors,
    get_mother_case_errors,
    get_mother_sex_errors,
    get_occupied_well_errors,
    get_repeated_case_name_errors,
    get_repeated_sample_name_errors,
    validate_concentration_in_case,
    validate_subject_ids_in_case,
)
from cg.store.store import Store


def validate_wells_contain_at_most_one_sample(order: TomteOrder) -> list[OccupiedWellError]:
    errors = []
    well_position_to_sample_map = create_well_position_to_sample_map(order)
    for indices in well_position_to_sample_map.values():
        if len(indices) > 1:
            well_errors = get_occupied_well_errors(indices[1:])
            errors.extend(well_errors)
    return errors


def create_well_position_to_sample_map(
    order: TomteOrder,
) -> dict[tuple[str, str], list[tuple[int, int]]]:
    """
    Constructs a dict with keys being a (container_name, well_position) pair. For each such pair, the value will be
    a list of (case index, sample index) pairs corresponding to all samples with matching container_name and
    well_position, provided the sample is on a plate.
    """
    well_position_to_sample_map = {}
    for case_index, case in order.enumerated_cases:
        for sample_index, sample in case.enumerated_samples:
            if _is_sample_on_plate(sample):
                key: tuple[str, str] = (sample.container_name, sample.well_position)
                value: tuple[int, int] = (case_index, sample_index)
                if not well_position_to_sample_map.get(key):
                    well_position_to_sample_map[key] = []
                well_position_to_sample_map[key].append(value)
    return well_position_to_sample_map


def validate_case_names_not_repeated(order: TomteOrder) -> list[RepeatedCaseNameError]:
    return get_repeated_case_name_errors(order)


def validate_sample_names_not_repeated(order: TomteOrder) -> list[RepeatedSampleNameError]:
    errors: list[RepeatedSampleNameError] = []
    for index, case in order.enumerated_cases:
        case_errors = get_repeated_sample_name_errors(case=case, case_index=index)
        errors.extend(case_errors)
    return errors


def validate_fathers_are_male(order: TomteOrder) -> list[InvalidFatherSexError]:
    errors: list[InvalidFatherSexError] = []
    for index, case in order.enumerated_cases:
        case_errors = get_father_sex_errors(case=case, case_index=index)
        errors.extend(case_errors)
    return errors


def validate_fathers_in_same_case_as_children(order: TomteOrder) -> list[FatherNotInCaseError]:
    errors = []
    for index, case in order.enumerated_cases:
        case_errors = get_father_case_errors(case=case, case_index=index)
        errors.extend(case_errors)
    return errors


def validate_mothers_are_female(order: TomteOrder) -> list[InvalidMotherSexError]:
    errors: list[InvalidMotherSexError] = []
    for index, case in order.enumerated_cases:
        case_errors = get_mother_sex_errors(case=case, case_index=index)
        errors.extend(case_errors)
    return errors


def validate_pedigree(order: TomteOrder) -> list[PedigreeError]:
    errors = []
    for case_index, case in order.enumerated_cases:
        case_errors = get_pedigree_errors(case=case, case_index=case_index)
        errors.extend(case_errors)
    return errors


def validate_mothers_in_same_case_as_children(order: TomteOrder) -> list[MotherNotInCaseError]:
    errors = []
    for index, case in order.enumerated_cases:
        case_errors = get_mother_case_errors(case=case, case_index=index)
        errors.extend(case_errors)
    return errors


def validate_subject_ids_different_from_case_names(
    order: TomteOrder,
) -> list[SubjectIdSameAsCaseNameError]:
    errors = []
    for index, case in order.enumerated_cases:
        case_errors = validate_subject_ids_in_case(case=case, case_index=index)
        errors.extend(case_errors)
    return errors


def validate_concentration_interval_if_skip_rc(
    order: TomteOrder, store: Store
) -> list[InvalidConcentrationIfSkipRCError]:
    if not order.skip_reception_control:
        return []
    errors = []
    for index, case in order.enumerated_cases:
        case_errors = validate_concentration_in_case(case=case, case_index=index, store=store)
        errors.extend(case_errors)
    return errors
