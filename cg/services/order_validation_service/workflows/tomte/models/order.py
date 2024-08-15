from cg.services.order_validation_service.models.order import Order
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase


class TomteOrder(Order):
    cases: list[TomteCase]

    @property
    def enumerated_cases(self) -> enumerate[TomteCase]:
        return enumerate(self.cases)

    @property
    def enumerated_new_cases(self) -> enumerate[TomteCase]:
        cases = []
        for case_index, case in self.enumerated_cases:
            if case.is_new:
                cases.append((case_index, case))
        return cases
