from cg.constants import PrepCategory
from cg.models.orders.sample_base import ContainerEnum
from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.workflows.tomte.models.sample import (
    TomteSample,
)
from cg.store.models import Application
from cg.store.store import Store


def _is_order_name_required(order: Order) -> bool:
    return False if order.connect_to_ticket else not order.name


def _is_ticket_number_missing(order: Order) -> bool:
    return order.connect_to_ticket and not order.ticket_number


def _is_application_not_compatible(
    allowed_prep_categories: list[PrepCategory], application_tag: str, store: Store
):
    application: Application = store.get_application_by_tag(application_tag)
    return application and application.prep_category not in allowed_prep_categories


def is_concentration_missing(sample: TomteSample) -> bool:
    return not sample.concentration_ng_ul


def is_well_position_missing(sample: TomteSample) -> bool:
    return sample.container == ContainerEnum.plate and not sample.well_position
