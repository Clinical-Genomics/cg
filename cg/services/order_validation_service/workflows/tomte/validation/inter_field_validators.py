from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.models.errors import OccupiedWellError, ValidationError
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample


def validate_wells_contain_at_most_one_sample(order: TomteOrder) -> list[OccupiedWellError]:
    errors: list[ValidationError] = []
    plate_samples: list[TomteSample] = _get_plate_samples(order)
    colliding_samples: list[TomteSample] = _get_colliding_samples(plate_samples)
    return _get_errors(colliding_samples)


def _get_errors(colliding_samples: list[TomteSample]) -> list[OccupiedWellError]:
    errors: list[OccupiedWellError] = []
    for sample in colliding_samples:
        error = OccupiedWellError(sample_id=sample.internal_id)
        errors.append(error)
    return errors

def _get_plate_samples(order: TomteOrder) -> list[TomteSample]:
    return [
        sample
        for case in order.cases
        for sample in case.samples
        if sample.container == ContainerEnum.plate
    ]


def _get_colliding_samples(samples: list[TomteSample]) -> list[TomteSample]:
    colliding_samples = []
    sample_well_map = _get_sample_well_map(samples)
    for _, well_samples in sample_well_map.items():
        if len(well_samples) > 1:
            colliding_samples.extend(well_samples[1:])
    return colliding_samples

def _get_sample_well_map(plate_samples: list[TomteSample]) -> dict[int, list[TomteSample]]:
    sample_well_map: dict[int, list[TomteSample]] = {}
    for sample in plate_samples:
        if sample.well_position not in sample_well_map:
            sample_well_map[sample.well_position] = []
        sample_well_map[sample.well_position].append(sample)
    return sample_well_map
