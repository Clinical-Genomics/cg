from collections import Counter

import re

from cg.services.order_validation_service.errors.sample_errors import (
    OccupiedWellError,
    WellPositionMissingError,
)
from cg.services.order_validation_service.models.order_with_samples import OrderWithNonHumanSamples
from cg.services.order_validation_service.models.sample import Sample


class PlateSamplesValidator:

    def __init__(self, order: OrderWithNonHumanSamples):
        self.wells: dict[tuple[str, str], list[int]] = {}
        self.plate_samples: list[tuple[int, Sample]] = []
        self._initialize_wells(order)

    def _initialize_wells(self, order: OrderWithNonHumanSamples):
        """
        Construct a dict with keys being a (container_name, well_position) pair.
        The value will be a list of sample indices for samples located in the well.
        """
        for sample_index, sample in order.enumerated_samples:
            if sample.is_on_plate:
                self.plate_samples.append((sample_index, sample))
                key: tuple[str, str] = (sample.container_name, sample.well_position)
                if not self.wells.get(key):
                    self.wells[key] = []
                self.wells[key].append(sample_index)

    def get_occupied_well_errors(self) -> list[OccupiedWellError]:
        """Get errors for samples assigned to wells that are already occupied."""
        conflicting_samples: list[Sample] = []
        for samples_indices in self.wells.values():
            if len(samples_indices) > 1:
                conflicting_samples.extend(samples_indices[1:])
        return get_occupied_well_errors(conflicting_samples)

    def get_well_position_missing_errors(self) -> list[OccupiedWellError]:
        """Get errors for samples missing well positions."""
        samples_missing_wells: list[int] = []
        for sample_index, sample in self.plate_samples:
            if not sample.well_position:
                samples_missing_wells.append(sample_index)
        return get_missing_well_errors(samples_missing_wells)


def get_occupied_well_errors(sample_indices: list[int]) -> list[OccupiedWellError]:
    return [OccupiedWellError(sample_index=sample_index) for sample_index in sample_indices]


def get_missing_well_errors(sample_indices: list[int]) -> list[WellPositionMissingError]:
    return [WellPositionMissingError(sample_index) for sample_index in sample_indices]


def get_indices_for_repeated_sample_names(order: OrderWithNonHumanSamples) -> list[int]:
    counter = Counter([sample.name for sample in order.samples])
    indices: list[int] = []
    for index, sample in order.enumerated_samples:
        if counter.get(sample.name) > 1:
            indices.append(index)
    return indices


def get_indices_for_tube_repeated_container_name(order: OrderWithNonHumanSamples) -> list[int]:
    counter = Counter([sample.container_name for sample in order.samples])
    indices: list[int] = []
    for index, sample in order.enumerated_samples:
        if sample.container_name == "Tube" and counter.get(sample.container_name) > 1:
            indices.append(index)
    return indices


def is_invalid_well_format(sample: Sample) -> bool:
    """Check if a sample has an invalid well format."""
    correct_well_position_pattern: str = r"^[A-H]:([1-9]|1[0-2])$"
    if sample.is_on_plate:
        return not bool(re.match(correct_well_position_pattern, sample.well_position))
    return False
