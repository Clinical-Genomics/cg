from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.errors.case_sample_errors import WellPositionMissingError
from cg.services.order_validation_service.errors.sample_errors import OccupiedWellError
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.microsalt.models.sample import MicrosaltSample


class PlateSamples:

    def __init__(self, order: MicrosaltOrder):
        self.wells: dict = {}
        self.plate_samples: list[tuple[MicrosaltSample, int]] = []
        self._initialize_plate(order)

    def _initialize_plate(self, order: MicrosaltOrder):
        for sample_index, sample in order.enumerated_new_samples:
            if is_sample_on_plate(sample):
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
        return get_well_errors(conflicting_samples)

    def get_well_position_missing_errors(self) -> list[OccupiedWellError]:
        """Get errors for samples missing well positions."""
        samples_missing_wells: list[int] = []
        for sample, sample_index in self.plate_samples:
            if not sample.well_position:
                samples_missing_wells.append(sample_index)
        return get_missing_well_errors(samples_missing_wells)


def get_well_errors(sample_indices: list[int]) -> list[OccupiedWellError]:
    return [OccupiedWellError(sample_index=sample_index) for sample_index in sample_indices]


def get_missing_well_errors(sample_indices: list[int]) -> list[OccupiedWellError]:
    return [WellPositionMissingError(sample_index=sample_index) for sample_index in sample_indices]


def is_sample_on_plate(sample: MicrosaltSample) -> bool:
    return sample.container == ContainerEnum.plate
