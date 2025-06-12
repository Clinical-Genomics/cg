from cg.models.orders.constants import OrderType
from cg.services.orders.validation.errors.sample_errors import (
    ApplicationArchivedError,
    ApplicationNotCompatibleError,
    ApplicationNotValidError,
    BufferInvalidError,
    CaptureKitInvalidError,
    CaptureKitMissingError,
    ConcentrationInvalidIfSkipRCError,
    ConcentrationRequiredError,
    ContainerNameMissingError,
    ContainerNameRepeatedError,
    IndexNumberMissingError,
    IndexNumberOutOfRangeError,
    InvalidVolumeError,
    OccupiedWellError,
    PoolApplicationError,
    PoolPriorityError,
    SampleError,
    SampleNameNotAvailableControlError,
    SampleNameRepeatedError,
    VolumeRequiredError,
    WellFormatError,
    WellFormatRmlError,
    WellPositionMissingError,
    WellPositionRmlMissingError,
)
from cg.services.orders.validation.models.order_aliases import (
    OrderWithControlSamples,
    OrderWithIndexedSamples,
)
from cg.services.orders.validation.models.sample_aliases import IndexedSample
from cg.services.orders.validation.order_types.fastq.models.order import FastqOrder
from cg.services.orders.validation.order_types.microsalt.models.order import OrderWithSamples
from cg.services.orders.validation.rules.sample.utils import (
    PlateSamplesValidator,
    get_indices_for_repeated_sample_names,
    get_indices_for_tube_repeated_container_name,
    get_sample_name_not_available_errors,
    has_multiple_applications,
    has_multiple_priorities,
    is_container_name_missing,
    is_index_number_missing,
    is_index_number_out_of_range,
    is_invalid_well_format,
    is_invalid_well_format_rml,
    validate_buffers_are_allowed,
    validate_concentration_interval,
    validate_concentration_required,
)
from cg.services.orders.validation.rules.utils import (
    is_application_compatible,
    is_invalid_capture_kit,
    is_sample_missing_capture_kit,
    is_volume_invalid,
    is_volume_missing,
)
from cg.store.store import Store


def validate_application_compatibility(
    order: OrderWithSamples,
    store: Store,
    **kwargs,
) -> list[ApplicationNotCompatibleError]:
    """
    Validate that the applications of all samples in the order are compatible with the order type.
    Applicable to all order types.
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
    """
    Validate that the applications of all samples in the order exist in the database.
    Applicable to all order types.
    """
    errors: list[ApplicationNotValidError] = []
    for sample_index, sample in order.enumerated_samples:
        if not store.get_application_by_tag(sample.application):
            error = ApplicationNotValidError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_applications_not_archived(
    order: OrderWithSamples, store: Store, **kwargs
) -> list[ApplicationArchivedError]:
    """
    Validate that none of the applications of the samples in the order are archived.
    Applicable to all order types.
    """
    errors: list[ApplicationArchivedError] = []
    for sample_index, sample in order.enumerated_samples:
        if store.is_application_archived(sample.application):
            error = ApplicationArchivedError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_buffer_skip_rc_condition(order: FastqOrder, **kwargs) -> list[BufferInvalidError]:
    """
    Validate that the sample buffers allow skipping reception control if that option is true.
    Only applicable to order types that have targeted sequencing applications (TGS).
    """
    errors: list[BufferInvalidError] = []
    if order.skip_reception_control:
        errors.extend(validate_buffers_are_allowed(order))
    return errors


def validate_capture_kit_compatible(
    order: FastqOrder, store: Store, **kwargs
) -> list[CaptureKitInvalidError]:
    """Validates that the capture kit is in our Bed table, and active."""
    errors: list[CaptureKitInvalidError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_invalid_capture_kit(sample=sample, store=store):
            error = CaptureKitInvalidError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_capture_kit_required(
    order: FastqOrder, store: Store, **kwargs
) -> list[CaptureKitMissingError]:
    """Validates that capture kit is required for TGS samples"""
    errors: list[CaptureKitMissingError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_sample_missing_capture_kit(sample=sample, store=store):
            error = CaptureKitMissingError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_concentration_interval_if_skip_rc(
    order: FastqOrder, store: Store, **kwargs
) -> list[ConcentrationInvalidIfSkipRCError]:
    """
    Validate that all samples have an allowed concentration if the order skips reception control.
    Only applicable to order types that have targeted sequencing applications (TGS).
    """
    errors: list[ConcentrationInvalidIfSkipRCError] = []
    if order.skip_reception_control:
        errors.extend(validate_concentration_interval(order=order, store=store))
    return errors


def validate_concentration_required_if_skip_rc(
    order: FastqOrder, **kwargs
) -> list[ConcentrationRequiredError]:
    """
    Validate that all samples have a concentration if the order skips reception control.
    Only applicable to order types that have targeted sequencing applications (TGS).
    """
    errors: list[ConcentrationRequiredError] = []
    if order.skip_reception_control:
        errors.extend(validate_concentration_required(order))
    return errors


def validate_container_name_required(
    order: OrderWithSamples, **kwargs
) -> list[ContainerNameMissingError]:
    """
    Validate that the container names are present for all samples sent on plates.
    Applicable to all order types.
    """
    errors: list[ContainerNameMissingError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_container_name_missing(sample=sample):
            error = ContainerNameMissingError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_index_number_in_range(
    order: OrderWithIndexedSamples, **kwargs
) -> list[IndexNumberOutOfRangeError]:
    errors: list[IndexNumberOutOfRangeError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_index_number_out_of_range(sample):
            error = IndexNumberOutOfRangeError(sample_index=sample_index, index=sample.index)
            errors.append(error)
    return errors


def validate_index_number_required(
    order: OrderWithIndexedSamples, **kwargs
) -> list[IndexNumberMissingError]:
    errors: list[IndexNumberMissingError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_index_number_missing(sample):
            error = IndexNumberMissingError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_non_control_sample_names_available(
    order: OrderWithControlSamples, store: Store, **kwargs
) -> list[SampleNameNotAvailableControlError]:
    """
    Validate that non-control sample names do not exists in the database under the same customer.
    Applicable to all orders with control samples.
    """
    errors: list[SampleNameNotAvailableControlError] = get_sample_name_not_available_errors(
        order=order, store=store, has_order_control=True
    )
    return errors


def validate_pools_contain_one_application(
    order: OrderWithIndexedSamples, **kwargs
) -> list[PoolApplicationError]:
    """
    Validate that the pools in the order contain only samples with the same application.
    Only applicable to order types with indexed samples (RML and Fluffy).
    """
    errors: list[PoolApplicationError] = []
    for pool, enumerated_samples in order.enumerated_pools.items():
        samples: list[IndexedSample] = [sample for _, sample in enumerated_samples]
        if has_multiple_applications(samples):
            for sample_index, _ in enumerated_samples:
                error = PoolApplicationError(sample_index=sample_index, pool_name=pool)
                errors.append(error)
    return errors


def validate_pools_contain_one_priority(
    order: OrderWithIndexedSamples, **kwargs
) -> list[PoolPriorityError]:
    """
    Validate that the pools in the order contain only samples with the same priority.
    Only applicable to order types with indexed samples (RML and Fluffy).
    """
    errors: list[PoolPriorityError] = []
    for pool, enumerated_samples in order.enumerated_pools.items():
        samples: list[IndexedSample] = [sample for _, sample in enumerated_samples]
        if has_multiple_priorities(samples):
            for sample_index, _ in enumerated_samples:
                error = PoolPriorityError(sample_index=sample_index, pool_name=pool)
                errors.append(error)
    return errors


def validate_sample_names_available(
    order: OrderWithSamples, store: Store, **kwargs
) -> list[SampleError]:
    """
    Validate that the sample names do not exists in the database under the same customer.
    Applicable to all orders without control samples.
    """
    errors: list[SampleError] = get_sample_name_not_available_errors(
        order=order, store=store, has_order_control=False
    )
    return errors


def validate_sample_names_unique(
    order: OrderWithSamples, **kwargs
) -> list[SampleNameRepeatedError]:
    """
    Validate that all the sample names are unique within the order.
    Applicable to all order types.
    """
    sample_indices: list[int] = get_indices_for_repeated_sample_names(order)
    return [SampleNameRepeatedError(sample_index=sample_index) for sample_index in sample_indices]


def validate_tube_container_name_unique(
    order: OrderWithSamples,
    **kwargs,
) -> list[ContainerNameRepeatedError]:
    """
    Validate that the container names are unique for tube samples within the order.
    Applicable to all order types.
    """
    errors: list[ContainerNameRepeatedError] = []
    repeated_container_name_indices: list = get_indices_for_tube_repeated_container_name(order)
    for sample_index in repeated_container_name_indices:
        error = ContainerNameRepeatedError(sample_index=sample_index)
        errors.append(error)
    return errors


def validate_volume_interval(order: OrderWithSamples, **kwargs) -> list[InvalidVolumeError]:
    """
    Validate that the volume of all samples is within the allowed interval.
    Applicable to all order types.
    """
    errors: list[InvalidVolumeError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_volume_invalid(sample):
            error = InvalidVolumeError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_volume_required(order: OrderWithSamples, **kwargs) -> list[VolumeRequiredError]:
    """
    Validate that all samples have a volume if they are in a container.
    Applicable to all order types.
    """
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
    """
    Validate that the wells in the order contain at most one sample.
    Applicable to all order types with non-indexed samples.
    """
    plate_samples = PlateSamplesValidator(order)
    return plate_samples.get_occupied_well_errors()


def validate_well_position_format(order: OrderWithSamples, **kwargs) -> list[WellFormatError]:
    """
    Validate that the well positions of all samples sent in plates have the correct format.
    Applicable to all order types with non-indexed samples.
    """
    errors: list[WellFormatError] = []
    for sample_index, sample in order.enumerated_samples:
        if is_invalid_well_format(sample=sample):
            error = WellFormatError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_well_position_rml_format(
    order: OrderWithIndexedSamples, **kwargs
) -> list[WellFormatRmlError]:
    """
    Validate that the well positions of all indexed samples have the correct format.
    Applicable to all order types with indexed samples.
    """
    errors: list[WellFormatRmlError] = []
    for sample_index, sample in order.enumerated_samples:
        if sample.well_position_rml and is_invalid_well_format_rml(sample=sample):
            error = WellFormatRmlError(sample_index=sample_index)
            errors.append(error)
    return errors


def validate_well_positions_required(
    order: OrderWithSamples,
    **kwargs,
) -> list[WellPositionMissingError]:
    """
    Validate that all samples sent in plates have well positions.
    Applicable to all order types with non-indexed samples
    """
    plate_samples = PlateSamplesValidator(order)
    return plate_samples.get_well_position_missing_errors()


def validate_well_positions_required_rml(
    order: OrderWithIndexedSamples, **kwargs
) -> list[WellPositionRmlMissingError]:
    """
    Validate that all indexed samples have well positions.
    Applicable to all order types with indexed samples.
    """
    errors: list[WellPositionRmlMissingError] = []
    for sample_index, sample in order.enumerated_samples:
        if sample.is_on_plate and not sample.well_position_rml:
            error = WellPositionRmlMissingError(sample_index=sample_index)
            errors.append(error)
    return errors
