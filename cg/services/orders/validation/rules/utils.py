from cg.constants.sample_sources import SourceType
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum
from cg.services.orders.validation.constants import MAXIMUM_VOLUME, MINIMUM_VOLUME
from cg.services.orders.validation.models.sample import Sample
from cg.services.orders.validation.models.sample_aliases import (
    SampleWithCaptureKit,
    SampleWithSkipRC,
)
from cg.store.models import Application
from cg.store.store import Store


def is_volume_invalid(sample: Sample) -> bool:
    in_container: bool = is_in_container(sample.container)
    allowed_volume: bool = is_volume_within_allowed_interval(sample.volume)
    return in_container and not allowed_volume


def is_in_container(container: ContainerEnum) -> bool:
    return container != ContainerEnum.no_container


def is_volume_within_allowed_interval(volume: int) -> bool:
    return volume and (MINIMUM_VOLUME <= volume <= MAXIMUM_VOLUME)


def is_sample_on_plate(sample: Sample) -> bool:
    return sample.container == ContainerEnum.plate


def is_application_compatible(
    order_type: OrderType,
    application_tag: str,
    store: Store,
) -> bool:
    application: Application | None = store.get_application_by_tag(application_tag)
    return not application or order_type in application.order_types


def is_volume_missing(sample: Sample) -> bool:
    """Check if a sample is missing its volume."""
    if is_in_container(sample.container) and not sample.volume:
        return True
    return False


def has_sample_invalid_concentration(
    sample: SampleWithSkipRC, allowed_interval: tuple[float, float]
) -> bool:
    concentration: float | None = sample.concentration_ng_ul
    return concentration and not is_sample_concentration_within_interval(
        concentration=concentration, interval=allowed_interval
    )


def get_concentration_interval(
    sample: SampleWithSkipRC, application: Application
) -> tuple[float, float] | None:
    is_cfdna: bool = is_sample_cfdna(sample)
    allowed_interval: tuple[float, float] = get_application_concentration_interval(
        application=application, is_cfdna=is_cfdna
    )
    return allowed_interval


def is_sample_cfdna(sample: SampleWithSkipRC) -> bool:
    source = sample.source
    return source == SourceType.CELL_FREE_DNA


def get_application_concentration_interval(
    application: Application, is_cfdna: bool
) -> tuple[float, float]:
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


def does_sample_need_capture_kit(sample: SampleWithCaptureKit, store: Store) -> bool:
    application: Application | None = store.get_application_by_tag(sample.application)
    return (
        application
        and application.prep_category == SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING
    )


def is_sample_missing_capture_kit(sample: SampleWithCaptureKit, store: Store) -> bool:
    """Returns whether a TGS sample has an application and is missing a capture kit."""
    return does_sample_need_capture_kit(sample=sample, store=store) and not sample.capture_kit


def is_invalid_capture_kit(sample: SampleWithCaptureKit, store: Store) -> bool:
    if not sample.capture_kit:
        return False
    valid_beds: list[str] = [bed.name for bed in store.get_active_beds()]
    return sample.capture_kit not in valid_beds
