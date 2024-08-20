from cg.services.order_validation_service.errors.sample_errors import (
    OccupiedWellError,
    WellPositionMissingError,
)
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.microsalt.models.sample import MicrosaltSample


class PlateSamplesValidator:

    def __init__(self, order: MicrosaltOrder):
        self.wells: dict[tuple[str, str], list[int]] = {}
        self.plate_samples: list[tuple[int, MicrosaltSample]] = []
        self._initialize_wells(order)

    def _initialize_wells(self, order: MicrosaltOrder):
        """
        Construct a dict with keys being a (container_name, well_position) pair.
        The value will be a list of sample indices for samples located in the well.
        """
        for sample_index, sample in order.enumerated_new_samples:
            if sample.is_on_plate:
                self.plate_samples.append((sample_index, sample))
                key: tuple[str, str] = (sample.container_name, sample.well_position)
                if not self.wells.get(key):
                    self.wells[key] = []
                self.wells[key].append(sample_index)

    def get_occupied_well_errors(self) -> list[OccupiedWellError]:
        """Get errors for samples assigned to wells that are already occupied."""
        conflicting_samples: list[MicrosaltSample] = []
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
