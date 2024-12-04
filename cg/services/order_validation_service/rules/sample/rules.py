from cg.models.orders.constants import OrderType
from cg.services.order_validation_service.constants import ALLOWED_SKIP_RC_BUFFERS
from cg.services.order_validation_service.errors.sample_errors import (
    ApplicationArchivedError,
    ApplicationNotCompatibleError,
    ApplicationNotValidError,
    ConcentrationRequiredError,
    ContainerNameMissingError,
    ContainerNameRepeatedError,
    InvalidBufferError,
    InvalidConcentrationIfSkipRCError,
    InvalidVolumeError,
    OccupiedWellError,
    OrganismDoesNotExistError,
    SampleNameNotAvailableError,
    SampleNameRepeatedError,
    VolumeRequiredError,
    WellFormatError,
    WellPositionMissingError,
)
from cg.services.order_validation_service.rules.sample.utils import (
    PlateSamplesValidator,
    get_indices_for_repeated_sample_names,
    get_indices_for_tube_repeated_container_name,
    is_container_name_missing,
    is_invalid_well_format,
    validate_concentration_interval,
    validate_concentration_required,
)
from cg.services.order_validation_service.rules.utils import (
    is_application_compatible,
    is_volume_invalid,
    is_volume_missing,
)
from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.order_validation_service.workflows.microsalt.models.order import OrderWithSamples
from cg.store.store import Store


def validate_application_compatibility(
    order: OrderWithSamples,
    store: Store,
    **kwargs,
) -> list[ApplicationNotCompatibleError]:
    """
    Validate that the applications of all samples in the order are compatible with the order type.
    """
    errors: list[ApplicationNotCompatibleError] = []
    order_type: OrderType = order.order_type
    for sample_index, sample in order.enumerated_samples:
        compatible: bool = is_application_compatible(
            order_type=order_type,
            application_tag=sample.application,
            store=store,
        )
        if not compatible:
            error = ApplicationNotCompatibleError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_application_exists(
    order: OrderWithSamples, store: Store, **kwargs
) -> list[ApplicationNotValidError]:
    """Validate that the applications of all samples in the order exist in the database."""
    errors: list[ApplicationNotValidError] = []
    for sample_index, sample in order.enumerated_samples:
        if not store.get_application_by_tag(sample.application):
            error = ApplicationNotValidError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_applications_not_archived(
    order: OrderWithSamples, store: Store, **kwargs
) -> list[ApplicationArchivedError]:
    errors: list[ApplicationArchivedError] = []
    for sample_index, sample in order.enumerated_samples:
        if store.is_application_archived(sample.application):
            error = ApplicationArchivedError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_buffer_skip_rc_condition(order: FastqOrder, **kwargs) -> list[InvalidBufferError]:
    errors: list[InvalidBufferError] = []
    if order.skip_reception_control:
        errors.extend(validate_buffers_are_allowed(order))
    return errors


def validate_buffers_are_allowed(order: FastqOrder) -> list[InvalidBufferError]:
    errors: list[InvalidBufferError] = []
    for sample_index, sample in order.enumerated_samples:
        if sample.elution_buffer not in ALLOWED_SKIP_RC_BUFFERS:
            error = InvalidBufferError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_concentration_interval_if_skip_rc(
    order: FastqOrder, store: Store, **kwargs
) -> list[InvalidConcentrationIfSkipRCError]:
    errors: list[InvalidConcentrationIfSkipRCError] = []
    if order.skip_reception_control:
        errors.extend(validate_concentration_interval(order=order, store=store))
    return errors


def validate_container_name_required(
    order: OrderWithSamples, **kwargs
) -> list[ContainerNameMissingError]:
    errors: list[ContainerNameMissingError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_container_name_missing(sample=sample):
            error = ContainerNameMissingError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_concentration_required_if_skip_rc(
    order: FastqOrder, **kwargs
) -> list[ConcentrationRequiredError]:
    errors: list[ConcentrationRequiredError] = []
    if order.skip_reception_control:
        errors.extend(validate_concentration_required(order))
    return errors


def validate_organism_exists(
    order: OrderWithSamples, store: Store, **kwargs
) -> list[OrganismDoesNotExistError]:
    errors: list[OrganismDoesNotExistError] = []
    for sample_index, sample in order.enumerated_samples:
        if not store.get_organism_by_internal_id(sample.organism):
            error = OrganismDoesNotExistError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_sample_names_available(
    order: OrderWithSamples, store: Store, **kwargs
) -> list[SampleNameNotAvailableError]:
    """Validate that the sample names do not exists in the database under the same customer."""
    errors: list[SampleNameNotAvailableError] = []
    customer = store.get_customer_by_internal_id(order.customer)
    for sample_index, sample in order.enumerated_samples:
        if store.get_sample_by_customer_and_name(
            sample_name=sample.name, customer_entry_id=[customer.id]
        ):
            error = SampleNameNotAvailableError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_sample_names_unique(
    order: OrderWithSamples, **kwargs
) -> list[SampleNameRepeatedError]:
    sample_indices: list[int] = get_indices_for_repeated_sample_names(order)
    return [SampleNameRepeatedError(sample_index=sample_index) for sample_index in sample_indices]


def validate_tube_container_name_unique(
    order: OrderWithSamples,
    **kwargs,
) -> list[ContainerNameRepeatedError]:
    """Validate that the container names are unique for tube samples."""
    errors: list[ContainerNameRepeatedError] = []
    repeated_container_name_indices: list = get_indices_for_tube_repeated_container_name(order)
    for sample_index in repeated_container_name_indices:
        error = ContainerNameRepeatedError(sample_index=sample_index)
        errors.append(error)
    return errors


def validate_volume_interval(order: OrderWithSamples, **kwargs) -> list[InvalidVolumeError]:
    errors: list[InvalidVolumeError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_volume_invalid(sample):
            error = InvalidVolumeError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_volume_required(order: OrderWithSamples, **kwargs) -> list[VolumeRequiredError]:
    errors: list[VolumeRequiredError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_volume_missing(sample):
            error = VolumeRequiredError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_wells_contain_at_most_one_sample(
    order: OrderWithSamples,
    **kwargs,
) -> list[OccupiedWellError]:
    plate_samples = PlateSamplesValidator(order)
    return plate_samples.get_occupied_well_errors()


def validate_well_position_format(order: OrderWithSamples, **kwargs) -> list[WellFormatError]:
    errors: list[WellFormatError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_invalid_well_format(sample=sample):
            error = WellFormatError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_well_positions_required(
    order: OrderWithSamples,
    **kwargs,
) -> list[WellPositionMissingError]:
    plate_samples = PlateSamplesValidator(order)
    return plate_samples.get_well_position_missing_errors()
