from collections import Counter

import re

from cg.constants.sample_sources import SourceType
from cg.constants.subject import Sex
from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.errors.case_errors import (
    RepeatedCaseNameError,
)
from cg.services.order_validation_service.errors.case_sample_errors import (
    FatherNotInCaseError,
    InvalidConcentrationIfSkipRCError,
    InvalidFatherSexError,
    InvalidMotherSexError,
    MotherNotInCaseError,
    OccupiedWellError,
    SampleNameRepeatedError,
    SubjectIdSameAsCaseNameError,
)
from cg.services.order_validation_service.models.aliases import (
    CaseContainingRelatives,
    SampleWithRelatives,
)
from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.models.order_with_cases import OrderWithCases
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.rules.utils import (
    is_in_container,
    is_sample_on_plate,
    is_volume_within_allowed_interval,
)
from cg.store.models import Application
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


def is_volume_missing(sample: Sample) -> bool:
    """Check if a sample has an invalid volume."""
    if is_in_container(sample.container) and not sample.volume:
        return True
    return False


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
    counter = Counter([case.name for case in order.cases])
    indices: list[int] = []

    for index, case in order.enumerated_new_cases:
        if counter.get(case.name) > 1:
            indices.append(index)

    return indices


def get_repeated_case_name_errors(order: OrderWithCases) -> list[RepeatedCaseNameError]:
    case_indices: list[int] = get_indices_for_repeated_case_names(order)
    return [RepeatedCaseNameError(case_index=case_index) for case_index in case_indices]


def get_indices_for_repeated_sample_names(case: Case) -> list[int]:
    counter = Counter([sample.name for sample in case.samples])
    indices: list[int] = []

    for index, sample in case.enumerated_new_samples:
        if counter.get(sample.name) > 1:
            indices.append(index)

    return indices


def get_repeated_sample_name_errors(case: Case, case_index: int) -> list[SampleNameRepeatedError]:
    sample_indices: list[int] = get_indices_for_repeated_sample_names(case)
    return [
        SampleNameRepeatedError(sample_index=sample_index, case_index=case_index)
        for sample_index in sample_indices
    ]


def get_father_sex_errors(
    case: CaseContainingRelatives, case_index: int
) -> list[InvalidFatherSexError]:
    errors: list[InvalidFatherSexError] = []
    children: list[tuple[SampleWithRelatives, int]] = case.get_samples_with_father()
    for child, child_index in children:
        if is_father_sex_invalid(child=child, case=case):
            error: InvalidFatherSexError = create_father_sex_error(
                case_index=case_index, sample_index=child_index
            )
            errors.append(error)
    return errors


def is_father_sex_invalid(child: SampleWithRelatives, case: CaseContainingRelatives) -> bool:
    father: SampleWithRelatives | None = case.get_sample(child.father)
    return father and father.sex != Sex.MALE


def create_father_sex_error(case_index: int, sample_index: int) -> InvalidFatherSexError:
    return InvalidFatherSexError(case_index=case_index, sample_index=sample_index)


def get_father_case_errors(
    case: CaseContainingRelatives,
    case_index: int,
) -> list[FatherNotInCaseError]:
    errors: list[FatherNotInCaseError] = []
    children: list[tuple[SampleWithRelatives, int]] = case.get_samples_with_father()
    for child, child_index in children:
        father: SampleWithRelatives | None = case.get_sample(child.father)
        if not father:
            error: FatherNotInCaseError = create_father_case_error(
                case_index=case_index,
                sample_index=child_index,
            )
            errors.append(error)
    return errors


def get_mother_sex_errors(
    case: CaseContainingRelatives,
    case_index: int,
) -> list[InvalidMotherSexError]:
    errors: list[InvalidMotherSexError] = []
    children: list[tuple[SampleWithRelatives, int]] = case.get_samples_with_mother()
    for child, child_index in children:
        if is_mother_sex_invalid(child=child, case=case):
            error: InvalidMotherSexError = create_mother_sex_error(
                case_index=case_index,
                sample_index=child_index,
            )
            errors.append(error)
    return errors


def get_mother_case_errors(
    case: CaseContainingRelatives,
    case_index: int,
) -> list[MotherNotInCaseError]:
    errors: list[MotherNotInCaseError] = []
    children: list[tuple[SampleWithRelatives, int]] = case.get_samples_with_mother()
    for child, child_index in children:
        mother: SampleWithRelatives | None = case.get_sample(child.mother)
        if not mother:
            error: MotherNotInCaseError = create_mother_case_error(
                case_index=case_index, sample_index=child_index
            )
            errors.append(error)
    return errors


def create_father_case_error(case_index: int, sample_index: int) -> FatherNotInCaseError:
    return FatherNotInCaseError(case_index=case_index, sample_index=sample_index)


def create_mother_case_error(case_index: int, sample_index: int) -> MotherNotInCaseError:
    return MotherNotInCaseError(case_index=case_index, sample_index=sample_index)


def is_mother_sex_invalid(child: SampleWithRelatives, case: CaseContainingRelatives) -> bool:
    mother: SampleWithRelatives | None = case.get_sample(child.mother)
    return mother and mother.sex != Sex.FEMALE


def create_mother_sex_error(case_index: int, sample_index: int) -> InvalidMotherSexError:
    return InvalidMotherSexError(case_index=case_index, sample_index=sample_index)


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
    case: CaseContainingRelatives, case_index: int, store: Store
) -> list[InvalidConcentrationIfSkipRCError]:
    errors: list[InvalidConcentrationIfSkipRCError] = []
    for sample_index, sample in case.enumerated_new_samples:
        if has_sample_invalid_concentration(sample=sample, store=store):
            error: InvalidConcentrationIfSkipRCError = create_invalid_concentration_error(
                case_index=case_index,
                sample=sample,
                sample_index=sample_index,
                store=store,
            )
            errors.append(error)
    return errors


def create_invalid_concentration_error(
    case_index: int, sample: SampleWithRelatives, sample_index: int, store: Store
) -> InvalidConcentrationIfSkipRCError:
    application: Application = store.get_application_by_tag(sample.application)
    is_cfdna: bool = is_sample_cfdna(sample)
    allowed_interval: tuple[float, float] = get_concentration_interval(
        application=application,
        is_cfdna=is_cfdna,
    )
    return InvalidConcentrationIfSkipRCError(
        case_index=case_index,
        sample_index=sample_index,
        allowed_interval=allowed_interval,
    )


def has_sample_invalid_concentration(sample: SampleWithRelatives, store: Store) -> bool:
    application: Application | None = store.get_application_by_tag(sample.application)
    if not application:
        return False
    concentration: float | None = sample.concentration_ng_ul
    is_cfdna: bool = is_sample_cfdna(sample)
    allowed_interval: tuple[float, float] = get_concentration_interval(
        application=application, is_cfdna=is_cfdna
    )
    return not is_sample_concentration_within_interval(
        concentration=concentration, interval=allowed_interval
    )


def is_sample_cfdna(sample: SampleWithRelatives) -> bool:
    source = sample.source
    return source == SourceType.CELL_FREE_DNA


def get_concentration_interval(application: Application, is_cfdna: bool) -> tuple[float, float]:
    if is_cfdna:
        return (
            application.sample_concentration_minimum_cfdna,
            application.sample_concentration_maximum_cfdna,
        )
    return application.sample_concentration_minimum, application.sample_concentration_maximum


def is_sample_concentration_within_interval(
    concentration: float, interval: tuple[float, float]
) -> bool:
    return interval[0] <= concentration <= interval[1]


def is_invalid_plate_well_format(sample: Sample) -> bool:
    """Check if a sample has an invalid well format."""
    correct_well_position_pattern: str = r"^[A-H]:([1-9]|1[0-2])$"
    if sample.is_on_plate:
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
