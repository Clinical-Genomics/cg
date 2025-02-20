import re
from collections import Counter

from cg.models.orders.sample_base import ContainerEnum, ControlEnum
from cg.services.orders.validation.constants import ALLOWED_SKIP_RC_BUFFERS, IndexEnum
from cg.services.orders.validation.errors.sample_errors import (
    BufferInvalidError,
    ConcentrationInvalidIfSkipRCError,
    ConcentrationRequiredError,
    OccupiedWellError,
    SampleError,
    SampleNameNotAvailableControlError,
    SampleNameNotAvailableError,
    WellPositionMissingError,
)
from cg.services.orders.validation.index_sequences import INDEX_SEQUENCES
from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.models.sample_aliases import IndexedSample
from cg.services.orders.validation.order_types.fastq.models.order import FastqOrder
from cg.services.orders.validation.order_types.fastq.models.sample import FastqSample
from cg.services.orders.validation.rules.utils import (
    get_application_concentration_interval,
    get_concentration_interval,
    has_sample_invalid_concentration,
    is_sample_cfdna,
)
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


def get_sample_name_not_available_errors(
    order: OrderWithSamples, store: Store, has_order_control: bool
) -> list[SampleError]:
    """Return errors for non-control samples with names already used in the database."""
    errors: list[SampleError] = []
    customer = store.get_customer_by_internal_id(order.customer)
    for sample_index, sample in order.enumerated_samples:
        if store.get_sample_by_customer_and_name(
            sample_name=sample.name, customer_entry_id=[customer.id]
        ):
            if is_sample_name_allowed_to_be_repeated(has_control=has_order_control, sample=sample):
                continue
            error = get_appropriate_sample_name_available_error(
                has_control=has_order_control, sample_index=sample_index
            )
            errors.append(error)
    return errors


def is_sample_name_allowed_to_be_repeated(has_control: bool, sample: Sample) -> bool:
    """
    Return whether a sample name can be used if it is already in the database.
    This is the case when the order has control samples and the sample is a control.
    """
    return has_control and sample.control in [ControlEnum.positive, ControlEnum.negative]


def get_appropriate_sample_name_available_error(
    has_control: bool, sample_index: int
) -> SampleError:
    """
    Return the appropriate error for a sample name that is not available based on whether the
    order has control samples or not.
    """
    if has_control:
        return SampleNameNotAvailableControlError(sample_index=sample_index)
    return SampleNameNotAvailableError(sample_index=sample_index)


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


def is_invalid_well_format_rml(sample: IndexedSample) -> bool:
    """Check if an indexed sample has an invalid well format."""
    correct_well_position_pattern: str = r"^[A-H]:([1-9]|1[0-2])$"
    return not bool(re.match(correct_well_position_pattern, sample.well_position_rml))


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
            allowed_interval: tuple[float, float] = get_concentration_interval(
                sample=sample, application=application
            )
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


def has_multiple_applications(samples: list[IndexedSample]) -> bool:
    return len({sample.application for sample in samples}) > 1


def has_multiple_priorities(samples: list[IndexedSample]) -> bool:
    return len({sample.priority for sample in samples}) > 1


def is_index_number_missing(sample: IndexedSample) -> bool:
    """Checks if a sample is missing its index number.
    Note: Index is an attribute on the sample, not its position in the list of samples."""
    return sample.index != IndexEnum.NO_INDEX and not sample.index_number


def is_index_number_out_of_range(sample: IndexedSample) -> bool:
    """Validates that the sample's index number is in range for its specified index.
    Note: Index number is an attribute on the sample, not its position in the list of samples."""
    return sample.index_number and not (
        1 <= sample.index_number <= len(INDEX_SEQUENCES[sample.index])
    )


def validate_buffers_are_allowed(order: FastqOrder) -> list[BufferInvalidError]:
    """
    Validate that the order has only samples with buffers that allow to skip reception control.
    We can only allow skipping reception control if there is no need to exchange buffer,
    so if the sample has nuclease-free water or Tris-HCL as buffer.
    """
    errors: list[BufferInvalidError] = []
    for sample_index, sample in order.enumerated_samples:
        if sample.elution_buffer not in ALLOWED_SKIP_RC_BUFFERS:
            error = BufferInvalidError(sample_index=sample_index)
            errors.append(error)
    return errors
