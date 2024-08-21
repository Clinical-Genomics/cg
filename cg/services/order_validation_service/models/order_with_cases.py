from cg.services.order_validation_service.models.case import Case
from cg.services.order_validation_service.models.order import Order


class OrderWithCases(Order):
    cases: list[Case]

    @property
    def enumerated_cases(self) -> enumerate[Case]:
        return enumerate(self.cases)

    @property
    def enumerated_new_cases(self) -> list[tuple[int, Case]]:
        cases: list[tuple[int, Case]] = []
        for case_index, case in self.enumerated_cases:
            if case.is_new:
                cases.append((case_index, case))
        return cases

    @property
    def enumerated_existing_cases(self) -> list[tuple[int, Case]]:
        cases: list[tuple[int, Case]] = []
        for case_index, case in self.enumerated_cases:
            if not case.is_new:
                cases.append((case_index, case))
        return cases
