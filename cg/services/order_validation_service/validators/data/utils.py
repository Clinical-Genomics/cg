from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.constants import (
    MAXIMUM_VOLUME,
    MINIMUM_VOLUME,
)
from cg.services.order_validation_service.models.sample import Sample
from cg.store.store import Store


def get_invalid_panels(panels: list[str], store: Store) -> list[str]:
    invalid_panels: list[str] = [
        panel for panel in panels if not store.does_gene_panel_exist(panel)
    ]
    return invalid_panels


def contains_duplicates(input_list: list) -> bool:
    return len(set(input_list)) != len(input_list)


def is_volume_invalid(sample: Sample) -> bool:
    in_container: bool = is_in_container(sample.container)
    allowed_volume: bool = is_volume_within_allowed_interval(sample.volume)
    return in_container and not allowed_volume


def is_in_container(container: ContainerEnum) -> bool:
    return container != ContainerEnum.no_container


def is_volume_within_allowed_interval(volume: int) -> bool:
    return MINIMUM_VOLUME <= volume <= MAXIMUM_VOLUME
