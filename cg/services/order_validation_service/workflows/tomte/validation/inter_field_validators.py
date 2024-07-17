from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.models.errors import OccupiedWellError, OrderError
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase


def validate_wells_contain_at_most_one_sample(order: TomteOrder) -> list[OccupiedWellError]:
    samples_with_cases = _get_plate_samples(order)
    samples = _get_colliding_samples(samples_with_cases)
    return _get_errors(samples)


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


def _get_colliding_samples(
    samples_with_cases: list[tuple[TomteSample, TomteCase]]
) -> list[tuple[TomteSample, TomteCase]]:
    colliding_samples = []
    sample_well_map = _get_sample_well_map(samples_with_cases)
    for _, well_samples in sample_well_map.items():
        if len(well_samples) > 1:
            colliding_samples.extend(well_samples[1:])
    return colliding_samples


def _get_sample_well_map(plate_samples_with_cases: list[tuple[TomteSample, str]]):
    sample_well_map: dict[str, tuple[TomteSample, TomteCase]] = {}
    for sample, case in plate_samples_with_cases:
        if sample.well_position not in sample_well_map:
            sample_well_map[sample.well_position] = []
        sample_well_map[sample.well_position].append((sample, case))
    return sample_well_map
