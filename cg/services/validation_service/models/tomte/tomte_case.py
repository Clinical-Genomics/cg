from cg.constants import GenePanelMasterList
from cg.models.orders.orderform_schema import OrderCase


class TomteCase(OrderCase):
    cohorts: list[str] | None = None
    panels: list[GenePanelMasterList]
    synopsis: str | None = None
