from pydantic import Field

from cg.constants import DataDelivery, GenePanelMasterList
from cg.constants.priority import PriorityTerms
from cg.models.orders.orderform_schema import OrderCase
from cg.models.orders.sample_base import NAME_PATTERN
from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.workflows.tomte.constants import TomteDeliveryType
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample


class TomteCase(Case):
    cohorts: list[str] | None = None
    data_delivery: TomteDeliveryType
    panels: list[GenePanelMasterList]
    synopsis: str | None = None
    samples: list[TomteSample]
