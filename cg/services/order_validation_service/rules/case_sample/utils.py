from cg.constants.constants import PrepCategory
from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.constants import MAXIMUM_VOLUME, MINIMUM_VOLUME
from cg.services.order_validation_service.models.sample import Sample
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample
from cg.store.models import Application
from cg.store.store import Store


def is_application_not_compatible(
    allowed_prep_categories: list[PrepCategory],
    application_tag: str,
    store: Store,
) -> bool:
    application: Application = store.get_application_by_tag(application_tag)
    return application and (application.prep_category not in allowed_prep_categories)


def is_concentration_missing(sample: TomteSample) -> bool:
    return not sample.concentration_ng_ul


def is_well_position_missing(sample: TomteSample) -> bool:
    return sample.container == ContainerEnum.plate and not sample.well_position


def is_container_name_missing(sample: TomteSample) -> bool:
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


def is_in_container(container: ContainerEnum) -> bool:
    return container != ContainerEnum.no_container


def is_volume_within_allowed_interval(volume: int) -> bool:
    return MINIMUM_VOLUME <= volume <= MAXIMUM_VOLUME
