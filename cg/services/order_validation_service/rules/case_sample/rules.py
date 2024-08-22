from cg.constants.constants import PrepCategory, Workflow
from cg.services.order_validation_service.constants import (
    ALLOWED_SKIP_RC_BUFFERS,
    WORKFLOW_PREP_CATEGORIES,
)
from cg.services.order_validation_service.errors.case_errors import InvalidGenePanelsError
from cg.services.order_validation_service.errors.case_sample_errors import (
    ApplicationArchivedError,
    ApplicationNotCompatibleError,
    ApplicationNotValidError,
    ConcentrationRequiredIfSkipRCError,
    ContainerNameMissingError,
    FatherNotInCaseError,
    InvalidBufferError,
    InvalidConcentrationIfSkipRCError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    InvalidVolumeError,
    MotherNotInCaseError,
    OccupiedWellError,
    PedigreeError,
    SampleDoesNotExistError,
    SampleNameRepeatedError,
    SexMissingError,
    SourceMissingError,
    StatusMissingError,
    SubjectIdSameAsCaseNameError,
    SubjectIdSameAsSampleNameError,
    WellPositionMissingError,
)
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.rules.case_sample.pedigree.validate_pedigree import (
    get_pedigree_errors,
)
from cg.services.order_validation_service.rules.case_sample.utils import (
    get_father_case_errors,
    get_father_sex_errors,
    get_invalid_panels,
    get_mother_case_errors,
    get_mother_sex_errors,
    get_occupied_well_errors,
    get_repeated_sample_name_errors,
    get_well_sample_map,
    is_application_not_compatible,
    is_concentration_missing,
    is_container_name_missing,
    is_volume_invalid,
    is_well_position_missing,
    validate_concentration_in_case,
    validate_subject_ids_in_case,
)
from cg.store.models import Sample
from cg.store.store import Store


def validate_application_compatibility(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[ApplicationNotCompatibleError]:
    errors: list[ApplicationNotCompatibleError] = []
    workflow: Workflow = order.workflow
    allowed_prep_categories: list[PrepCategory] = WORKFLOW_PREP_CATEGORIES[workflow]
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_application_not_compatible(
                allowed_prep_categories=allowed_prep_categories,
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


def validate_samples_exist(
    order: OrderWithCases,
    store: Store,
    **kwargs,
) -> list[SampleDoesNotExistError]:
    errors: list[SampleDoesNotExistError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_existing_samples:
            sample: Sample | None = store.get_sample_by_internal_id(sample.internal_id)
            if not sample:
                error = SampleDoesNotExistError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_sex_required_for_new_samples(order: OrderWithCases, **kwargs) -> list[SexMissingError]:
    errors: list[SexMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not sample.sex:
                error = SexMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors


def validate_source_required(order: OrderWithCases, **kwargs) -> list[SourceMissingError]:
    errors: list[SourceMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not sample.source:
                error = SourceMissingError(case_index=case_index, sample_index=sample_index)
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
    order: OrderWithCases, **kwargs
) -> list[SampleNameRepeatedError]:
    errors: list[SampleNameRepeatedError] = []
    for index, case in order.enumerated_new_cases:
        case_errors: list[SampleNameRepeatedError] = get_repeated_sample_name_errors(
            case=case, case_index=index
        )
        errors.extend(case_errors)
    return errors


def validate_fathers_are_male(order: OrderWithCases, **kwargs) -> list[InvalidFatherSexError]:
    errors: list[InvalidFatherSexError] = []
    for index, case in order.enumerated_cases:
        case_errors: list[InvalidFatherSexError] = get_father_sex_errors(
            case=case, case_index=index
        )
        errors.extend(case_errors)
    return errors


def validate_fathers_in_same_case_as_children(
    order: OrderWithCases, **kwargs
) -> list[FatherNotInCaseError]:
    errors: list[FatherNotInCaseError] = []
    for index, case in order.enumerated_cases:
        case_errors: list[FatherNotInCaseError] = get_father_case_errors(
            case=case,
            case_index=index,
        )
        errors.extend(case_errors)
    return errors


def validate_mothers_are_female(order: OrderWithCases, **kwargs) -> list[InvalidMotherSexError]:
    errors: list[InvalidMotherSexError] = []
    for index, case in order.enumerated_cases:
        case_errors: list[InvalidMotherSexError] = get_mother_sex_errors(
            case=case,
            case_index=index,
        )
        errors.extend(case_errors)
    return errors


def validate_mothers_in_same_case_as_children(
    order: OrderWithCases, **kwargs
) -> list[MotherNotInCaseError]:
    errors: list[MotherNotInCaseError] = []
    for index, case in order.enumerated_cases:
        case_errors: list[MotherNotInCaseError] = get_mother_case_errors(
            case=case,
            case_index=index,
        )
        errors.extend(case_errors)
    return errors


def validate_pedigree(order: OrderWithCases, **kwargs) -> list[PedigreeError]:
    errors: list[PedigreeError] = []
    for case_index, case in order.enumerated_cases:
        case_errors: list[PedigreeError] = get_pedigree_errors(case=case, case_index=case_index)
        errors.extend(case_errors)
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


def validate_status_required_if_new(order: OrderWithCases, **kwargs) -> list[StatusMissingError]:
    errors: list[StatusMissingError] = []
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if not sample.status:
                error = StatusMissingError(case_index=case_index, sample_index=sample_index)
                errors.append(error)
    return errors
