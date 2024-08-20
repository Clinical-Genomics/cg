from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.errors.sample_errors import OccupiedWellError
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.microsalt.models.sample import MicrosaltSample


class PlateSamples:

    def __init__(self, order: MicrosaltOrder):
        self.wells: dict = {}
        self._initialize_map(order)

    def _initialize_map(self, order: MicrosaltOrder):
        for sample_index, sample in order.enumerated_new_samples:
            if is_sample_on_plate(sample):
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


def get_well_errors(sample_indices: list[int]) -> list[OccupiedWellError]:
    return [OccupiedWellError(sample_index=sample_index) for sample_index in sample_indices]


def is_sample_on_plate(sample: MicrosaltSample) -> bool:
    return sample.container == ContainerEnum.plate
