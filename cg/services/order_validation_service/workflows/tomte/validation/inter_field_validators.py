from cg.models.orders.sample_base import ContainerEnum, SexEnum
from cg.services.order_validation_service.models.errors import (
    InvalidFatherSexError,
    InvalidMotherSexError,
    OccupiedWellError,
)
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample


def validate_fathers_are_male(order: TomteOrder) -> list[InvalidFatherSexError]:
    return [
        InvalidFatherSexError(sample_id=sample.internal_id, case_id=case.internal_id)
        for case in order.cases
        for sample in case.samples
        if _invalid_father_sex(sample)
    ]


def _invalid_father_sex(sample: TomteSample) -> bool:
    return sample.father and sample.sex != SexEnum.male


def validate_mothers_are_female(order: TomteOrder) -> list[InvalidMotherSexError]:
    return [
        InvalidMotherSexError(sample_id=sample.internal_id, case_id=case.internal_id)
        for case in order.cases
        for sample in case.samples
        if _invalid_mother_sex(sample)
    ]


def _invalid_mother_sex(sample: TomteSample) -> bool:
    return sample.mother and sample.sex != SexEnum.female


def validate_wells_contain_at_most_one_sample(order: TomteOrder) -> list[OccupiedWellError]:
    plate_samples_with_cases: list[tuple[TomteSample, str]] = _get_plate_samples(order)
    colliding_samples: list[tuple[TomteSample, str]] = _get_colliding_samples(
        plate_samples_with_cases
    )
    return _get_errors(colliding_samples)


def _get_errors(colliding_samples: list[tuple[TomteSample, str]]) -> list[OccupiedWellError]:
    errors: list[OccupiedWellError] = []
    for sample, case_id in colliding_samples:
        error = OccupiedWellError(sample_id=sample.internal_id, case_id=case_id)
        errors.append(error)
    return errors


def _get_plate_samples(order: TomteOrder) -> list[tuple[TomteSample, str]]:
    return [
        (sample, case.internal_id)
        for case in order.cases
        for sample in case.samples
        if sample.container == ContainerEnum.plate
    ]


def _get_colliding_samples(
    samples_with_cases: list[tuple[TomteSample, str]]
) -> list[tuple[TomteSample, str]]:
    colliding_samples = []
    sample_well_map = _get_sample_well_map(samples_with_cases)
    for _, well_samples in sample_well_map.items():
        if len(well_samples) > 1:
            colliding_samples.extend(well_samples[1:])
    return colliding_samples


def _get_sample_well_map(
    plate_samples_with_cases: list[tuple[TomteSample, str]]
) -> dict[int, list[tuple[TomteSample, str]]]:
    sample_well_map: dict[int, list[tuple[TomteSample, str]]] = {}
    for sample, case_id in plate_samples_with_cases:
        if sample.well_position not in sample_well_map:
            sample_well_map[sample.well_position] = []
        sample_well_map[sample.well_position].append((sample, case_id))
    return sample_well_map
