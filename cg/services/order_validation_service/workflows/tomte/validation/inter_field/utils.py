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


def _get_errors(colliding_samples: list[tuple[TomteSample, TomteCase]]) -> list[OccupiedWellError]:
    errors = []
    for sample, case in colliding_samples:
        error = OccupiedWellError(sample_name=sample.name, case_name=case.name)
        errors.append(error)
    return errors


def _get_plate_samples(order: TomteOrder) -> list[tuple[TomteSample, TomteCase]]:
    return [
        (sample, case)
        for case in order.cases
        for sample in case.samples
        if _is_sample_on_plate(sample)
    ]


def _is_sample_on_plate(sample: TomteSample) -> bool:
    return sample.container == ContainerEnum.plate


def _get_excess_samples(
    samples_with_cases: list[tuple[TomteSample, TomteCase]]
) -> list[tuple[TomteSample, TomteCase]]:
    colliding_samples = []
    sample_well_map = _get_sample_well_map(samples_with_cases)
    for _, well_samples in sample_well_map.items():
        if len(well_samples) > 1:
            extra_samples_in_well = well_samples[1:]
            colliding_samples.extend(extra_samples_in_well)
    return colliding_samples


def _get_sample_well_map(plate_samples_with_cases: list[tuple[TomteSample, TomteCase]]):
    sample_well_map: dict[str, list[tuple[TomteSample, TomteCase]]] = {}
    for sample, case in plate_samples_with_cases:
        if sample.well_position not in sample_well_map:
            sample_well_map[sample.well_position] = []
        sample_well_map[sample.well_position].append((sample, case))
    return sample_well_map


def get_repeated_case_names(order: TomteOrder) -> list[str]:
    case_names = [case.name for case in order.cases]
    count = Counter(case_names)
    return [name for name, freq in count.items() if freq > 1]


def get_repeated_case_name_errors(order: TomteOrder) -> list[RepeatedCaseNameError]:
    case_names = get_repeated_case_names(order)
    return [RepeatedCaseNameError(case_name=name) for name in case_names]


def get_repeated_sample_names(case: TomteCase) -> list[str]:
    sample_names = [sample.name for sample in case.samples]
    count = Counter(sample_names)
    return [name for name, freq in count.items() if freq > 1]


def get_repeated_sample_name_errors(case: TomteCase) -> list[RepeatedSampleNameError]:
    sample_names = get_repeated_sample_names(case)
    return [RepeatedSampleNameError(sample_name=name, case_name=case.name) for name in sample_names]


def get_father_sex_errors(case: TomteCase) -> list[InvalidFatherSexError]:
    errors = []
    children: list[TomteSample] = case.get_samples_with_father()
    for child in children:
        if is_father_sex_invalid(child=child, case=case):
            error = create_father_sex_error(case=case, sample=child)
            errors.append(error)
    return errors


def is_father_sex_invalid(child: TomteSample, case: TomteCase) -> bool:
    father: TomteSample | None = case.get_sample(child.father)
    return father and father.sex != Sex.MALE


def create_father_sex_error(case: TomteCase, sample: TomteSample) -> InvalidFatherSexError:
    return InvalidFatherSexError(sample_name=sample.name, case_name=case.name)


def get_father_case_errors(case: TomteCase) -> list[FatherNotInCaseError]:
    errors = []
    children: list[TomteSample] = case.get_samples_with_father()
    for child in children:
        father: TomteSample | None = case.get_sample(child.father)
        if not father:
            error = create_father_case_error(case=case, sample=child)
            errors.append(error)
    return errors


def get_mother_sex_errors(case: TomteCase) -> list[InvalidMotherSexError]:
    errors = []
    children: list[TomteSample] = case.get_samples_with_mother()
    for child in children:
        if is_mother_sex_invalid(child=child, case=case):
            error = create_mother_sex_error(case=case, sample=child)
            errors.append(error)
    return errors


def get_mother_case_errors(case: TomteCase) -> list[MotherNotInCaseError]:
    errors = []
    children: list[TomteSample] = case.get_samples_with_mother()
    for child in children:
        mother: TomteSample | None = case.get_sample(child.mother)
        if not mother:
            error = create_mother_case_error(case=case, sample=child)
            errors.append(error)
    return errors


def create_father_case_error(case: TomteCase, sample: TomteSample) -> FatherNotInCaseError:
    return FatherNotInCaseError(case_name=case.name, sample_name=sample.name)


def create_mother_case_error(case: TomteCase, sample: TomteSample) -> MotherNotInCaseError:
    return MotherNotInCaseError(case_name=case.name, sample_name=sample.name)


def is_mother_sex_invalid(child: TomteSample, case: TomteCase) -> bool:
    mother: TomteSample | None = case.get_sample(child.mother)
    return mother and mother.sex != Sex.FEMALE


def create_mother_sex_error(case: TomteCase, sample: TomteSample) -> InvalidMotherSexError:
    return InvalidMotherSexError(sample_name=sample.name, case_name=case.name)


def validate_subject_ids_in_case(case: TomteCase) -> list[SubjectIdSameAsCaseNameError]:
    errors = []
    for sample in case.samples:
        if sample.subject_id == case.name:
            error = SubjectIdSameAsCaseNameError(case_name=case.name, sample_name=sample.name)
            errors.append(error)
    return errors


def validate_concentration_in_case(
    case: TomteCase, store: Store
) -> list[InvalidConcentrationIfSkipRCError]:
    errors = []
    for sample in case.samples:
        if has_sample_invalid_concentration(sample=sample, store=store):
            error = create_invalid_concentration_error(
                case_name=case.name, sample=sample, store=store
            )
            errors.append(error)
    return errors


def create_invalid_concentration_error(
    case_name: str, sample: TomteSample, store: Store
) -> InvalidConcentrationIfSkipRCError:
    application: Application = store.get_application_by_tag(sample.application)
    is_cfdna = is_sample_cfdna(sample)
    allowed_interval = get_concentration_interval(application=application, is_cfdna=is_cfdna)
    return InvalidConcentrationIfSkipRCError(
        case_name=case_name, sample_name=sample.name, allowed_interval=allowed_interval
    )


def has_sample_invalid_concentration(sample: TomteSample, store: Store) -> bool:
    application: Application | None = store.get_application_by_tag(sample.application)
    return not is_sample_concentration_allowed(sample=sample, application=application)


def is_sample_concentration_allowed(sample: TomteSample, application: Application):
    concentration = sample.concentration_ng_ul
    is_cfdna = is_sample_cfdna(sample)
    interval = get_concentration_interval(application=application, is_cfdna=is_cfdna)
    return is_sample_concentration_within_interval(concentration=concentration, interval=interval)


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
