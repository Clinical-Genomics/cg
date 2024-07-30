from collections import Counter
from cg.constants.subject import Sex
from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.models.errors import (
    InvalidFatherSexError,
    InvalidMotherCaseError,
    OccupiedWellError,
    RepeatedCaseNameError,
    RepeatedSampleNameError,
)
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.models.sample import (
    TomteSample,
)


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


def get_mother_case_errors(case: TomteCase) -> list[InvalidMotherCaseError]:
    errors = []
