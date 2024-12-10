import re
from collections import Counter

from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.errors.sample_errors import (
    ConcentrationInvalidIfSkipRCError,
    ConcentrationRequiredError,
    OccupiedWellError,
    WellPositionMissingError,
)
from cg.services.order_validation_service.models.order_with_samples import OrderWithSamples
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.rules.utils import (
    get_application_concentration_interval,
    get_concentration_interval,
    has_sample_invalid_concentration,
    is_sample_cfdna,
)
from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.order_validation_service.workflows.fastq.models.sample import FastqSample
from cg.store.models import Application
from cg.store.store import Store


class PlateSamplesValidator:

    def __init__(self, order: OrderWithSamples):
        self.wells: dict[tuple[str, str], list[int]] = {}
        self.plate_samples: list[tuple[int, Sample]] = []
        self._initialize_wells(order)

    def _initialize_wells(self, order: OrderWithSamples):
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
        conflicting_samples: list[int] = []
        for samples_indices in self.wells.values():
            if len(samples_indices) > 1:
                conflicting_samples.extend(samples_indices[1:])
        return get_occupied_well_errors(conflicting_samples)

    def get_well_position_missing_errors(self) -> list[WellPositionMissingError]:
        """Get errors for samples missing well positions."""
        samples_missing_wells: list[int] = []
        for sample_index, sample in self.plate_samples:
            if not sample.well_position:
                samples_missing_wells.append(sample_index)
        return get_missing_well_errors(samples_missing_wells)


def get_occupied_well_errors(sample_indices: list[int]) -> list[OccupiedWellError]:
    return [OccupiedWellError(sample_index=sample_index) for sample_index in sample_indices]


def get_missing_well_errors(sample_indices: list[int]) -> list[WellPositionMissingError]:
    return [WellPositionMissingError(sample_index=sample_index) for sample_index in sample_indices]


def get_indices_for_repeated_sample_names(order: OrderWithSamples) -> list[int]:
    counter = Counter([sample.name for sample in order.samples])
    indices: list[int] = []
    for index, sample in order.enumerated_samples:
        if counter.get(sample.name) > 1:
            indices.append(index)
    return indices


def is_tube_container_name_redundant(sample: Sample, counter: Counter) -> bool:
    return sample.container == ContainerEnum.tube and counter.get(sample.container_name) > 1


def get_indices_for_tube_repeated_container_name(order: OrderWithSamples) -> list[int]:
    counter = Counter([sample.container_name for sample in order.samples])
    indices: list[int] = []
    for index, sample in order.enumerated_samples:
        if is_tube_container_name_redundant(sample, counter):
            indices.append(index)
    return indices


def is_invalid_well_format(sample: Sample) -> bool:
    """Check if a sample has an invalid well format."""
    correct_well_position_pattern: str = r"^[A-H]:([1-9]|1[0-2])$"
    if sample.is_on_plate:
        return not bool(re.match(correct_well_position_pattern, sample.well_position))
    return False


def is_container_name_missing(sample: Sample) -> bool:
    """Checks if a sample is missing its container name."""
    if sample.is_on_plate and not sample.container_name:
        return True
    return False


def create_invalid_concentration_error(
    sample: FastqSample, sample_index: int, store: Store
) -> ConcentrationInvalidIfSkipRCError:
    application: Application = store.get_application_by_tag(sample.application)
    is_cfdna: bool = is_sample_cfdna(sample)
    allowed_interval: tuple[float, float] = get_application_concentration_interval(
        application=application,
        is_cfdna=is_cfdna,
    )
    return ConcentrationInvalidIfSkipRCError(
        sample_index=sample_index,
        allowed_interval=allowed_interval,
    )


def validate_concentration_interval(
    order: FastqOrder, store: Store
) -> list[ConcentrationInvalidIfSkipRCError]:
    errors: list[ConcentrationInvalidIfSkipRCError] = []
    for sample_index, sample in order.enumerated_samples:
        if application := store.get_application_by_tag(sample.application):
            allowed_interval = get_concentration_interval(sample=sample, application=application)
            if allowed_interval and has_sample_invalid_concentration(
                sample=sample, allowed_interval=allowed_interval
            ):
                error: ConcentrationInvalidIfSkipRCError = create_invalid_concentration_error(
                    sample=sample,
                    sample_index=sample_index,
                    store=store,
                )
                errors.append(error)
    return errors


def validate_concentration_required(order: FastqOrder) -> list[ConcentrationRequiredError]:
    errors: list[ConcentrationRequiredError] = []
    for sample_index, sample in order.enumerated_samples:
        if not sample.concentration_ng_ul:
            error = ConcentrationRequiredError(sample_index=sample_index)
            errors.append(error)
    return errors