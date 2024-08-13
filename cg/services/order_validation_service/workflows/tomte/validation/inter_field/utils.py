from collections import Counter

from cg.constants.sample_sources import SourceType
from cg.constants.subject import Sex
from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.models.errors import (
    FatherNotInCaseError,
    InvalidConcentrationIfSkipRCError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    MotherNotInCaseError,
    OccupiedWellError,
    RepeatedCaseNameError,
    RepeatedSampleNameError,
    SubjectIdSameAsCaseNameError,
)
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.models.sample import (
    TomteSample,
)
from cg.store.models import Application
from cg.store.store import Store


def get_occupied_well_errors(colliding_samples: list[tuple[int, int]]) -> list[OccupiedWellError]:
    errors = []
    for sample_index, case_index in colliding_samples:
        error = OccupiedWellError(case_index=case_index, sample_index=sample_index)
        errors.append(error)
    return errors


def _is_sample_on_plate(sample: TomteSample) -> bool:
    return sample.container == ContainerEnum.plate


def get_indices_for_repeated_case_names(order: TomteOrder) -> list[int]:
    case_names = [case.name for case in order.cases]
    count = Counter(case_names)
    return [
        case_index for case_index, case_name in enumerate(case_names) if count.get(case_name) > 1
    ]


def get_repeated_case_name_errors(order: TomteOrder) -> list[RepeatedCaseNameError]:
    case_indices = get_indices_for_repeated_case_names(order)
    return [RepeatedCaseNameError(case_index=case_index) for case_index in case_indices]


def get_indices_for_repeated_sample_names(case: TomteCase) -> list[int]:
    sample_names = [sample.name for sample in case.samples]
    count = Counter(sample_names)
    return [
        sample_index
        for sample_index, sample_name in enumerate(sample_names)
        if count.get(sample_name) > 1
    ]


def get_repeated_sample_name_errors(
    case: TomteCase, case_index: int
) -> list[RepeatedSampleNameError]:
    sample_indices = get_indices_for_repeated_sample_names(case)
    return [
        RepeatedSampleNameError(sample_index=sample_index, case_index=case_index)
        for sample_index in sample_indices
    ]


def get_father_sex_errors(case: TomteCase, case_index: int) -> list[InvalidFatherSexError]:
    errors = []
    children: list[tuple[TomteSample, int]] = case.get_samples_with_father()
    for child, child_index in children:
        if is_father_sex_invalid(child=child, case=case):
            error = create_father_sex_error(case_index=case_index, sample_index=child_index)
            errors.append(error)
    return errors


def is_father_sex_invalid(child: TomteSample, case: TomteCase) -> bool:
    father: TomteSample | None = case.get_sample(child.father)
    return father and father.sex != Sex.MALE


def create_father_sex_error(case_index: int, sample_index: int) -> InvalidFatherSexError:
    return InvalidFatherSexError(case_index=case_index, sample_index=sample_index)


def get_father_case_errors(case: TomteCase, case_index: int) -> list[FatherNotInCaseError]:
    errors = []
    children: list[tuple[TomteSample, int]] = case.get_samples_with_father()
    for child, child_index in children:
        father: TomteSample | None = case.get_sample(child.father)
        if not father:
            error = create_father_case_error(case_index=case_index, sample_index=child_index)
            errors.append(error)
    return errors


def get_mother_sex_errors(case: TomteCase, case_index: int) -> list[InvalidMotherSexError]:
    errors = []
    children: list[tuple[TomteSample, int]] = case.get_samples_with_mother()
    for child, child_index in children:
        if is_mother_sex_invalid(child=child, case=case):
            error = create_mother_sex_error(case_index=case_index, sample_index=child_index)
            errors.append(error)
    return errors


def get_mother_case_errors(case: TomteCase, case_index: int) -> list[MotherNotInCaseError]:
    errors = []
    children: list[tuple[TomteSample, int]] = case.get_samples_with_mother()
    for child, child_index in children:
        mother: TomteSample | None = case.get_sample(child.mother)
        if not mother:
            error = create_mother_case_error(case_index=case_index, sample_index=child_index)
            errors.append(error)
    return errors


def create_father_case_error(case_index: int, sample_index: int) -> FatherNotInCaseError:
    return FatherNotInCaseError(case_index=case_index, sample_index=sample_index)


def create_mother_case_error(case_index: int, sample_index: int) -> MotherNotInCaseError:
    return MotherNotInCaseError(case_index=case_index, sample_index=sample_index)


def is_mother_sex_invalid(child: TomteSample, case: TomteCase) -> bool:
    mother: TomteSample | None = case.get_sample(child.mother)
    return mother and mother.sex != Sex.FEMALE


def create_mother_sex_error(case_index: int, sample_index: int) -> InvalidMotherSexError:
    return InvalidMotherSexError(case_index=case_index, sample_index=sample_index)


def validate_subject_ids_in_case(
    case: TomteCase, case_index: int
) -> list[SubjectIdSameAsCaseNameError]:
    errors = []
    for sample_index, sample in case.enumerated_samples:
        if sample.subject_id == case.name:
            error = SubjectIdSameAsCaseNameError(case_index=case_index, sample_index=sample_index)
            errors.append(error)
    return errors


def validate_concentration_in_case(
    case: TomteCase, case_index: int, store: Store
) -> list[InvalidConcentrationIfSkipRCError]:
    errors = []
    for sample_index, sample in case.enumerated_samples:
        if has_sample_invalid_concentration(sample=sample, store=store):
            error = create_invalid_concentration_error(
                case_index=case_index, sample=sample, sample_index=sample_index, store=store
            )
            errors.append(error)
    return errors


def create_invalid_concentration_error(
    case_index: int, sample: TomteSample, sample_index: int, store: Store
) -> InvalidConcentrationIfSkipRCError:
    application: Application = store.get_application_by_tag(sample.application)
    is_cfdna = is_sample_cfdna(sample)
    allowed_interval = get_concentration_interval(application=application, is_cfdna=is_cfdna)
    return InvalidConcentrationIfSkipRCError(
        case_index=case_index, sample_index=sample_index, allowed_interval=allowed_interval
    )


def has_sample_invalid_concentration(sample: TomteSample, store: Store) -> bool:
    application: Application | None = store.get_application_by_tag(sample.application)
    concentration = sample.concentration_ng_ul
    is_cfdna = is_sample_cfdna(sample)
    allowed_interval = get_concentration_interval(application=application, is_cfdna=is_cfdna)
    return not is_sample_concentration_within_interval(
        concentration=concentration, interval=allowed_interval
    )


def is_sample_cfdna(sample: TomteSample):
    source = sample.source
    return source == SourceType.CELL_FREE_DNA


def get_concentration_interval(application: Application, is_cfdna: bool) -> tuple[int, int]:
    if is_cfdna:
        return (
            application.sample_concentration_minimum_cfdna,
            application.sample_concentration_maximum_cfdna,
        )
    return application.sample_concentration_minimum, application.sample_concentration_maximum


def is_sample_concentration_within_interval(concentration: float, interval: tuple[int, int]):
    return interval[0] <= concentration <= interval[1]
