from cg.constants import GenePanelMasterList
from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.workflows.tomte.constants import TomteDeliveryType
from cg.services.order_validation_service.workflows.tomte.models.sample import TomteSample


class TomteCase(Case):
    cohorts: list[str] | None = None
    data_delivery: TomteDeliveryType
    panels: list[GenePanelMasterList]
    synopsis: str | None = None
    samples: list[TomteSample]
