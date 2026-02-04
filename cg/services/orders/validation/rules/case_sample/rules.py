from collections import Counter

from cg.models.orders.constants import OrderType
from cg.services.orders.validation.constants import ALLOWED_SKIP_RC_BUFFERS
from cg.services.orders.validation.errors.case_errors import InvalidGenePanelsError
from cg.services.orders.validation.errors.case_sample_errors import (
    ApplicationArchivedError,
    ApplicationNotCompatibleError,
    ApplicationNotValidError,
    BufferMissingError,
    CaptureKitMissingError,
    CaptureKitResetError,
    ConcentrationRequiredIfSkipRCError,
    ContainerNameMissingError,
    ContainerNameRepeatedError,
    ExistingSampleWrongTypeError,
    FatherNotInCaseError,
    InvalidBufferError,
    InvalidCaptureKitError,
    InvalidConcentrationIfSkipRCError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    InvalidVolumeError,
    MotherNotInCaseError,
    OccupiedWellError,
    PedigreeError,
    SampleDoesNotExistError,
    SampleNameAlreadyExistsError,
    SampleNameRepeatedError,
    SampleNameSameAsCaseNameError,
    SampleOutsideOfCollaborationError,
    SexSubjectIdError,
    StatusUnknownError,
    SubjectIdSameAsCaseNameError,
    SubjectIdSameAsSampleNameError,
    VolumeRequiredError,
    WellFormatError,
    WellPositionMissingError,
)
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.models.sample_aliases import SampleInCase
from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.balsamic_umi.models.order import BalsamicUmiOrder
from cg.services.orders.validation.rules.case_sample.pedigree.validate_pedigree import (
    get_pedigree_errors,
)
from cg.services.orders.validation.rules.case_sample.utils import (
    are_all_samples_unknown,
    get_counter_container_names,
    get_existing_case_names,
    get_existing_sample_names,
    get_father_case_errors,
    get_father_sex_errors,
    get_invalid_panels,
    get_mother_case_errors,
    get_mother_sex_errors,
    get_occupied_well_errors,
    get_well_sample_map,
    has_sex_and_subject,
    is_buffer_missing,
    is_concentration_missing,
    is_container_name_missing,
    is_invalid_plate_well_format,
    is_sample_compatible_with_order_type,
    is_sample_not_from_collaboration,
    is_sample_tube_name_reused,
    is_well_position_missing,
    validate_concentration_in_case,
    validate_subject_ids_in_case,
)
from cg.services.orders.validation.rules.utils import (
    does_sample_need_capture_kit,
    is_application_compatible,
    is_invalid_capture_kit,
    is_sample_missing_capture_kit,
    is_volume_invalid,
    is_volume_missing,
)
from cg.store.models import Sample as DbSample
from cg.store.store import Store


def validate_application_compatibility(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[ApplicationNotCompatibleError]:
    errors: list[ApplicationNotCompatibleError] = []
    order_type: OrderType = order.order_type
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not is_application_compatible(
                order_type=order_type,
                application_tag=sample.application,
                store=store,
            ):
                error = ApplicationNotCompatibleError(
                    case_index=case_index,
                    sample_index=sample_index,
                )
                errors.append(error)
    return errors


def validate_buffer_skip_rc_condition(order: OrderWithCases, **kwargs) -> list[InvalidBufferError]:
    errors: list[InvalidBufferError] = []
    if order.skip_reception_control:
        errors.extend(validate_buffers_are_allowed(order))
    return errors


def validate_buffers_are_allowed(order: OrderWithCases, **kwargs) -> list[InvalidBufferError]:
    errors: list[InvalidBufferError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if sample.elution_buffer not in ALLOWED_SKIP_RC_BUFFERS:
                error = InvalidBufferError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_concentration_required_if_skip_rc(
    order: OrderWithCases, **kwargs
) -> list[ConcentrationRequiredIfSkipRCError]:
    if not order.skip_reception_control:
        return []
    errors: list[ConcentrationRequiredIfSkipRCError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_concentration_missing(sample):
                error = ConcentrationRequiredIfSkipRCError(
                    case_index=case_index,
                    sample_index=sample_index,
                )
                errors.append(error)
    return errors


def validate_subject_ids_different_from_sample_names(
    order: OrderWithCases, **kwargs
) -> list[SubjectIdSameAsSampleNameError]:
    errors: list[SubjectIdSameAsSampleNameError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if sample.name == sample.subject_id:
                error = SubjectIdSameAsSampleNameError(
                    case_index=case_index,
                    sample_index=sample_index,
                )
                errors.append(error)
    return errors


def validate_well_positions_required(
    order: OrderWithCases, **kwargs
) -> list[WellPositionMissingError]:
    errors: list[WellPositionMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_well_position_missing(sample):
                error = WellPositionMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_container_name_required(
    order: OrderWithCases, **kwargs
) -> list[ContainerNameMissingError]:
    errors: list[ContainerNameMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_container_name_missing(sample):
                error = ContainerNameMissingError(
                    case_index=case_index,
                    sample_index=sample_index,
                )
                errors.append(error)
    return errors


def validate_application_exists(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[ApplicationNotValidError]:
    errors: list[ApplicationNotValidError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not store.get_application_by_tag(sample.application):
                error = ApplicationNotValidError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_application_not_archived(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[ApplicationArchivedError]:
    errors: list[ApplicationArchivedError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if store.is_application_archived(sample.application):
                error = ApplicationArchivedError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_gene_panels_exist(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[InvalidGenePanelsError]:
    errors: list[InvalidGenePanelsError] = []
    for case_index, case in order.enumerated_new_cases:
        if invalid_panels := get_invalid_panels(panels=case.panels, store=store):
            case_error = InvalidGenePanelsError(case_index=case_index, panels=invalid_panels)
            errors.append(case_error)
    return errors


def validate_volume_interval(order: OrderWithCases, **kwargs) -> list[InvalidVolumeError]:
    errors: list[InvalidVolumeError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_volume_invalid(sample):
                error = InvalidVolumeError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_volume_required(order: OrderWithCases, **kwargs) -> list[VolumeRequiredError]:
    errors: list[VolumeRequiredError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_volume_missing(sample):
                error = VolumeRequiredError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_samples_exist(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[SampleDoesNotExistError]:
    errors: list[SampleDoesNotExistError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_existing_samples:
            sample: DbSample | None = store.get_sample_by_internal_id(sample.internal_id)
            if not sample:
                error = SampleDoesNotExistError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_wells_contain_at_most_one_sample(
    order: OrderWithCases, **kwargs
) -> list[OccupiedWellError]:
    errors: list[OccupiedWellError] = []
    well_position_to_sample_map: dict[tuple[str, str], list[tuple[int, int]]] = get_well_sample_map(
        order
    )
    for indices in well_position_to_sample_map.values():
        if len(indices) > 1:
            well_errors = get_occupied_well_errors(indices[1:])
            errors.extend(well_errors)
    return errors


def validate_sample_names_not_repeated(
    order: OrderWithCases, store: Store, **kwargs
) -> list[SampleNameRepeatedError]:
    """Ensures that sample names are unique within the order
    and that they not already used in the case previously."""
    old_sample_names: set[str] = get_existing_sample_names(order=order, status_db=store)
    new_samples: list[tuple[int, int, SampleInCase]] = order.enumerated_new_samples
    sample_name_counter = Counter([sample.name for _, _, sample in new_samples])
    return [
        SampleNameRepeatedError(case_index=case_index, sample_index=sample_index)
        for case_index, sample_index, sample in new_samples
        if sample_name_counter.get(sample.name) > 1 or sample.name in old_sample_names
    ]


def validate_sample_names_different_from_case_names(
    order: OrderWithCases, store: Store, **kwargs
) -> list[SampleNameSameAsCaseNameError]:
    """Return errors with the indexes of samples having the same name as any case in the order."""
    errors: list[SampleNameSameAsCaseNameError] = []
    new_case_names: set[str] = {case.name for _, case in order.enumerated_new_cases}
    existing_case_names: set[str] = get_existing_case_names(order=order, status_db=store)
    all_case_names = new_case_names.union(existing_case_names)
    for case_index, sample_index, sample in order.enumerated_new_samples:
        if sample.name in all_case_names:
            error = SampleNameSameAsCaseNameError(
                case_index=case_index,
                sample_index=sample_index,
            )
            errors.append(error)
    return errors


def validate_fathers_are_male(
    order: OrderWithCases, store: Store, **kwargs
) -> list[InvalidFatherSexError]:
    errors: list[InvalidFatherSexError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[InvalidFatherSexError] = get_father_sex_errors(
            case=case, case_index=index, store=store
        )
        errors.extend(case_errors)
    return errors


def validate_fathers_in_same_case_as_children(
    order: OrderWithCases, store: Store, **kwargs
) -> list[FatherNotInCaseError]:
    errors: list[FatherNotInCaseError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[FatherNotInCaseError] = get_father_case_errors(
            case=case, case_index=index, store=store
        )
        errors.extend(case_errors)
    return errors


def validate_mothers_are_female(
    order: OrderWithCases, store: Store, **kwargs
) -> list[InvalidMotherSexError]:
    errors: list[InvalidMotherSexError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[InvalidMotherSexError] = get_mother_sex_errors(
            case=case, case_index=index, store=store
        )
        errors.extend(case_errors)
    return errors


def validate_mothers_in_same_case_as_children(
    order: OrderWithCases, store: Store, **kwargs
) -> list[MotherNotInCaseError]:
    errors: list[MotherNotInCaseError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[MotherNotInCaseError] = get_mother_case_errors(
            case=case, case_index=index, store=store
        )
        errors.extend(case_errors)
    return errors


def validate_pedigree(order: OrderWithCases, store: Store, **kwargs) -> list[PedigreeError]:
    errors: list[PedigreeError] = []
    for case_index, case in order.enumerated_new_cases:
        case_errors: list[PedigreeError] = get_pedigree_errors(
            case=case, case_index=case_index, store=store
        )
        errors.extend(case_errors)
    return errors


def validate_subject_sex_consistency(
    order: OrderWithCases,
    store: Store,
) -> list[SexSubjectIdError]:
    errors: list[SexSubjectIdError] = []

    for case_index, sample_index, sample in order.enumerated_new_samples:
        if not has_sex_and_subject(sample):
            continue
        if store.sample_exists_with_different_sex(
            customer_internal_id=order.customer,
            subject_id=sample.subject_id,
            sex=sample.sex,
        ):
            error = SexSubjectIdError(
                case_index=case_index,
                sample_index=sample_index,
            )
            errors.append(error)
    return errors


def validate_subject_ids_different_from_case_names(
    order: OrderWithCases, **kwargs
) -> list[SubjectIdSameAsCaseNameError]:
    errors: list[SubjectIdSameAsCaseNameError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[SubjectIdSameAsCaseNameError] = validate_subject_ids_in_case(
            case=case,
            case_index=index,
        )
        errors.extend(case_errors)
    return errors


def validate_concentration_interval_if_skip_rc(
    order: OrderWithCases, store: Store, **kwargs
) -> list[InvalidConcentrationIfSkipRCError]:
    if not order.skip_reception_control:
        return []
    errors: list[InvalidConcentrationIfSkipRCError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[InvalidConcentrationIfSkipRCError] = validate_concentration_in_case(
            case=case,
            case_index=index,
            store=store,
        )
        errors.extend(case_errors)
    return errors


def validate_well_position_format(order: OrderWithCases, **kwargs) -> list[WellFormatError]:
    errors: list[WellFormatError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_invalid_plate_well_format(sample=sample):
                error = WellFormatError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_tube_container_name_unique(
    order: OrderWithCases, **kwargs
) -> list[ContainerNameRepeatedError]:
    errors: list[ContainerNameRepeatedError] = []

    container_name_counter: Counter = get_counter_container_names(order)

    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_sample_tube_name_reused(sample=sample, counter=container_name_counter):
                error = ContainerNameRepeatedError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_not_all_samples_unknown_in_case(
    order: OrderWithCases, **kwargs
) -> list[StatusUnknownError]:
    errors: list[StatusUnknownError] = []

    for case_index, case in order.enumerated_new_cases:
        if are_all_samples_unknown(case):
            for sample_index, _ in case.enumerated_samples:
                error = StatusUnknownError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_buffer_required(order: OrderWithCases, **kwargs) -> list[BufferMissingError]:
    """Return an error for each new sample missing a buffer, if its application requires one."""

    errors: list[BufferMissingError] = []
    for case_index, sample_index, sample in order.enumerated_new_samples:
        if is_buffer_missing(sample):
            error = BufferMissingError(case_index=case_index, sample_index=sample_index)
            errors.append(error)
    return errors


def reset_optional_capture_kits(
    order: BalsamicOrder | BalsamicUmiOrder, store: Store, **kwargs
) -> list[CaptureKitResetError]:
    """
    Sets the capture kit to None for each sample where it is set but not needed and returns an error
    to be rendered as a warning for each such sample.
    """
    errors: list[CaptureKitResetError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not does_sample_need_capture_kit(sample=sample, store=store) and sample.capture_kit:
                sample.capture_kit = None
                error = CaptureKitResetError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_capture_kit_requirement(
    order: BalsamicOrder | BalsamicUmiOrder, store: Store
) -> list[CaptureKitMissingError]:
    """
    Return an error for each new sample missing a capture kit, if its application requires one.
    Applicable to Balsamic and Balsamic-UMI orders only.
    """
    errors: list[CaptureKitMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_sample_missing_capture_kit(sample=sample, store=store):
                error = CaptureKitMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_capture_kit(
    order: BalsamicOrder | BalsamicUmiOrder, store: Store
) -> list[InvalidCaptureKitError]:
    errors: list[InvalidCaptureKitError] = []
    for case_index, sample_index, sample in order.enumerated_new_samples:
        if is_invalid_capture_kit(sample=sample, store=store):
            errors.append(InvalidCaptureKitError(sample_index=sample_index, case_index=case_index))

    return errors


def validate_existing_samples_belong_to_collaboration(
    order: OrderWithCases, store: Store, **kwargs
) -> list[SampleOutsideOfCollaborationError]:
    """Validates that existing samples belong to the same collaboration as the order's customer."""
    errors: list[SampleOutsideOfCollaborationError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_existing_samples:
            if is_sample_not_from_collaboration(
                customer_id=order.customer, sample=sample, store=store
            ):
                error = SampleOutsideOfCollaborationError(
                    sample_index=sample_index, case_index=case_index
                )
                errors.append(error)
    return errors


def validate_existing_samples_compatible_with_order_type(
    order: OrderWithCases, store: Store, **kwargs
) -> list[ExistingSampleWrongTypeError]:
    errors: list[ExistingSampleWrongTypeError] = []
    for case_index, sample_index, sample in order.enumerated_existing_samples:
        if not is_sample_compatible_with_order_type(
            order_type=order.order_type, sample=sample, store=store
        ):
            error = ExistingSampleWrongTypeError(case_index=case_index, sample_index=sample_index)
            errors.append(error)
    return errors


def validate_sample_names_available(
    order: OrderWithCases, store: Store, **kwargs
) -> list[SampleNameAlreadyExistsError]:
    """Validates that new sample names are not already used by the customer."""
    errors: list[SampleNameAlreadyExistsError] = []
    customer_entry_id: int = store.get_customer_by_internal_id(order.customer).id
    for case_index, sample_index, sample in order.enumerated_new_samples:
        if store.is_sample_name_used(sample=sample, customer_entry_id=customer_entry_id):
            error = SampleNameAlreadyExistsError(case_index=case_index, sample_index=sample_index)
            errors.append(error)
    return errors
