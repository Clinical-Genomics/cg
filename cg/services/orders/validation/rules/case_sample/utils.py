import re
from collections import Counter

from cg.constants.constants import StatusOptions
from cg.constants.subject import Sex
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, SexEnum
from cg.services.orders.validation.errors.case_errors import RepeatedCaseNameError
from cg.services.orders.validation.errors.case_sample_errors import (
    FatherNotInCaseError,
    InvalidConcentrationIfSkipRCError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    MotherNotInCaseError,
    OccupiedWellError,
    SubjectIdSameAsCaseNameError,
)
from cg.services.orders.validation.models.case import Case
from cg.services.orders.validation.models.case_aliases import (
    CaseContainingRelatives,
    CaseWithSkipRC,
)
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.models.sample_aliases import (
    HumanSample,
    SampleInCase,
    SampleWithRelatives,
)
from cg.services.orders.validation.rules.case.utils import is_sample_in_case
from cg.services.orders.validation.rules.utils import (
    get_concentration_interval,
    has_sample_invalid_concentration,
    is_in_container,
    is_sample_on_plate,
    is_volume_within_allowed_interval,
)
from cg.store.models import Customer
from cg.store.models import Sample as DbSample
from cg.store.store import Store


def is_concentration_missing(sample: SampleWithRelatives) -> bool:
    return not sample.concentration_ng_ul


def is_well_position_missing(sample: SampleWithRelatives) -> bool:
    return sample.container == ContainerEnum.plate and not sample.well_position


def is_container_name_missing(sample: SampleWithRelatives) -> bool:
    return sample.container == ContainerEnum.plate and not sample.container_name


def get_invalid_panels(panels: list[str], store: Store) -> list[str]:
    invalid_panels: list[str] = [
        panel for panel in panels if not store.does_gene_panel_exist(panel)
    ]
    return invalid_panels


def is_volume_invalid(sample: Sample) -> bool:
    in_container: bool = is_in_container(sample.container)
    allowed_volume: bool = is_volume_within_allowed_interval(sample.volume)
    return in_container and not allowed_volume


def get_well_sample_map(
    order: OrderWithCases, **kwargs
) -> dict[tuple[str, str], list[tuple[int, int]]]:
    """
    Constructs a dict with keys being a (container_name, well_position) pair. For each such pair, the value will be
    a list of (case index, sample index) pairs corresponding to all samples with matching container_name and
    well_position, provided the sample is on a plate.
    """
    well_position_to_sample_map = {}
    for case_index, case in order.enumerated_new_cases:
        for sample_index, sample in case.enumerated_new_samples:
            if is_sample_on_plate(sample):
                key: tuple[str, str] = (sample.container_name, sample.well_position)
                value: tuple[int, int] = (case_index, sample_index)
                if not well_position_to_sample_map.get(key):
                    well_position_to_sample_map[key] = []
                well_position_to_sample_map[key].append(value)
    return well_position_to_sample_map


def get_occupied_well_errors(colliding_samples: list[tuple[int, int]]) -> list[OccupiedWellError]:
    errors: list[OccupiedWellError] = []
    for case_index, sample_index in colliding_samples:
        error = OccupiedWellError(case_index=case_index, sample_index=sample_index)
        errors.append(error)
    return errors


def get_indices_for_repeated_case_names(order: OrderWithCases) -> list[int]:
    counter = Counter([case.name for _, case in order.enumerated_new_cases])
    indices: list[int] = []

    for index, case in order.enumerated_new_cases:
        if counter.get(case.name) > 1:
            indices.append(index)

    return indices


def get_repeated_case_name_errors(order: OrderWithCases) -> list[RepeatedCaseNameError]:
    case_indices: list[int] = get_indices_for_repeated_case_names(order)
    return [RepeatedCaseNameError(case_index=case_index) for case_index in case_indices]


def get_father_sex_errors(
    case: CaseContainingRelatives, case_index: int, store: Store
) -> list[InvalidFatherSexError]:
    errors: list[InvalidFatherSexError] = []
    children: list[tuple[SampleWithRelatives, int]] = case.get_samples_with_father()
    for child, child_index in children:
        if is_father_sex_invalid(child=child, case=case, store=store):
            error: InvalidFatherSexError = create_father_sex_error(
                case_index=case_index, sample_index=child_index
            )
            errors.append(error)
    return errors


def is_father_sex_invalid(
    child: SampleWithRelatives, case: CaseContainingRelatives, store: Store
) -> bool:
    father: SampleWithRelatives | None = case.get_new_sample(child.father)
    if not father:
        father: DbSample | None = case.get_existing_sample_from_db(
            sample_name=child.father, store=store
        )
    return father and father.sex != Sex.MALE


def create_father_sex_error(case_index: int, sample_index: int) -> InvalidFatherSexError:
    return InvalidFatherSexError(case_index=case_index, sample_index=sample_index)


def get_father_case_errors(
    case: CaseContainingRelatives, case_index: int, store: Store
) -> list[FatherNotInCaseError]:
    errors: list[FatherNotInCaseError] = []
    children: list[tuple[SampleWithRelatives | ExistingSample, int]] = (
        case.get_samples_with_father()
    )
    for child, child_index in children:
        if not is_sample_in_case(case=case, sample_name=child.father, store=store):
            error: FatherNotInCaseError = create_father_case_error(
                case_index=case_index,
                sample_index=child_index,
            )
            errors.append(error)
    return errors


def get_mother_sex_errors(
    case: CaseContainingRelatives, case_index: int, store: Store
) -> list[InvalidMotherSexError]:
    errors: list[InvalidMotherSexError] = []
    children: list[tuple[SampleWithRelatives, int]] = case.get_samples_with_mother()
    for child, child_index in children:
        if is_mother_sex_invalid(child=child, case=case, store=store):
            error: InvalidMotherSexError = create_mother_sex_error(
                case_index=case_index,
                sample_index=child_index,
            )
            errors.append(error)
    return errors


def get_mother_case_errors(
    case: CaseContainingRelatives, case_index: int, store: Store
) -> list[MotherNotInCaseError]:
    errors: list[MotherNotInCaseError] = []
    children: list[tuple[SampleWithRelatives, int]] = case.get_samples_with_mother()
    for child, child_index in children:
        if not is_sample_in_case(case=case, sample_name=child.mother, store=store):
            error: MotherNotInCaseError = create_mother_case_error(
                case_index=case_index, sample_index=child_index
            )
            errors.append(error)
    return errors


def create_father_case_error(case_index: int, sample_index: int) -> FatherNotInCaseError:
    return FatherNotInCaseError(case_index=case_index, sample_index=sample_index)


def create_mother_case_error(case_index: int, sample_index: int) -> MotherNotInCaseError:
    return MotherNotInCaseError(case_index=case_index, sample_index=sample_index)


def is_mother_sex_invalid(
    child: SampleWithRelatives, case: CaseContainingRelatives, store: Store
) -> bool:
    mother: SampleWithRelatives | None = case.get_new_sample(child.mother)
    if not mother:
        mother: DbSample | None = case.get_existing_sample_from_db(
            sample_name=child.mother, store=store
        )
    return mother and mother.sex != Sex.FEMALE


def create_mother_sex_error(case_index: int, sample_index: int) -> InvalidMotherSexError:
    return InvalidMotherSexError(case_index=case_index, sample_index=sample_index)


def has_sex_and_subject(sample: HumanSample) -> bool:
    return bool(sample.subject_id and sample.sex != SexEnum.unknown)


def validate_subject_ids_in_case(
    case: CaseContainingRelatives, case_index: int
) -> list[SubjectIdSameAsCaseNameError]:
    errors: list[SubjectIdSameAsCaseNameError] = []
    for sample_index, sample in case.enumerated_new_samples:
        if sample.subject_id == case.name:
            error = SubjectIdSameAsCaseNameError(case_index=case_index, sample_index=sample_index)
            errors.append(error)
    return errors


def validate_concentration_in_case(
    case: CaseWithSkipRC, case_index: int, store: Store
) -> list[InvalidConcentrationIfSkipRCError]:
    errors: list[InvalidConcentrationIfSkipRCError] = []
    for sample_index, sample in case.enumerated_new_samples:
        if application := store.get_application_by_tag(sample.application):
            allowed_interval = get_concentration_interval(sample=sample, application=application)
            if has_sample_invalid_concentration(sample=sample, allowed_interval=allowed_interval):
                error: InvalidConcentrationIfSkipRCError = create_invalid_concentration_error(
                    case_index=case_index,
                    sample_index=sample_index,
                    allowed_interval=allowed_interval,
                )
                errors.append(error)
    return errors


def create_invalid_concentration_error(
    case_index: int, sample_index: int, allowed_interval: tuple[float, float]
) -> InvalidConcentrationIfSkipRCError:
    return InvalidConcentrationIfSkipRCError(
        case_index=case_index,
        sample_index=sample_index,
        allowed_interval=allowed_interval,
    )


def is_invalid_plate_well_format(sample: Sample) -> bool:
    """Check if a sample has an invalid well format."""
    if sample.is_on_plate and sample.well_position:
        correct_well_position_pattern: str = r"^[A-H]:([1-9]|1[0-2])$"
        return not bool(re.match(correct_well_position_pattern, sample.well_position))
    return False


def is_sample_tube_name_reused(sample: Sample, counter: Counter) -> bool:
    """Check if a tube container name is reused across samples."""
    return sample.container == ContainerEnum.tube and counter.get(sample.container_name) > 1


def get_counter_container_names(order: OrderWithCases) -> Counter:
    counter = Counter(
        sample.container_name
        for case_index, case in order.enumerated_new_cases
        for sample_index, sample in case.enumerated_new_samples
    )
    return counter


def get_existing_sample_names(order: OrderWithCases, status_db: Store) -> set[str]:
    existing_sample_names: set[str] = set()
    for case in order.cases:
        if case.is_new:
            for sample_index, sample in case.enumerated_existing_samples:
                db_sample = status_db.get_sample_by_internal_id(sample.internal_id)
                existing_sample_names.add(db_sample.name)
        else:
            db_case = status_db.get_case_by_internal_id(case.internal_id)
            for sample in db_case.samples:
                existing_sample_names.add(sample.name)
    return existing_sample_names


def are_all_samples_unknown(case: Case) -> bool:
    """Check if all samples in a case are unknown."""
    return all(sample.status == StatusOptions.UNKNOWN for sample in case.samples)


def is_buffer_missing(sample: SampleInCase) -> bool:
    applications_requiring_buffer: tuple = ("PAN", "EX", "WGSWPF", "METWPF")
    return bool(
        sample.application.startswith(tuple(applications_requiring_buffer))
        and not sample.elution_buffer
    )


def is_sample_not_from_collaboration(
    customer_id: str, sample: ExistingSample, store: Store
) -> bool:
    db_sample: DbSample | None = store.get_sample_by_internal_id(sample.internal_id)
    customer: Customer | None = store.get_customer_by_internal_id(customer_id)
    return db_sample and customer and db_sample.customer not in customer.collaborators


def get_existing_case_names(order: OrderWithCases, status_db: Store) -> set[str]:
    existing_case_names: set[str] = set()
    for _, case in order.enumerated_existing_cases:
        if db_case := status_db.get_case_by_internal_id(case.internal_id):
            existing_case_names.add(db_case.name)
    return existing_case_names


def is_sample_compatible_with_order_type(
    order_type: OrderType, sample: ExistingSample, store: Store
) -> bool:
    if db_sample := store.get_sample_by_internal_id(sample.internal_id):
        return order_type in db_sample.application_version.application.order_types
    else:
        return True
