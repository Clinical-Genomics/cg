from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.workflows.tomte.models.sample import (
    TomteSample,
)
from cg.store.store import Store


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
