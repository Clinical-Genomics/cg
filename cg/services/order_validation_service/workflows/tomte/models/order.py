from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase


class TomteOrder(Order):
    cases: list[TomteCase]

    @property
    def enumerated_cases(self) -> enumerate[TomteCase]:
        return enumerate(self.cases)
