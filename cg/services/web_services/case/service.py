from cg.server.dto.cases.requests import CasesRequest
from cg.store.models import Case, Customer
from cg.store.store import Store


class CaseWebService:

    def __init__(self, store: Store):
        self.store = store

    def get_cases(
        self, request: CasesRequest, customers: list[Customer] | None
    ) -> tuple[list[dict], int]:
        """Return cases with links for a customer from the database."""
        cases, total = self._get_cases(request=request, customers=customers)
        cases_with_links: list[dict] = [case.to_dict(links=True) for case in cases]
        return cases_with_links, total

    def _get_cases(
        self, request: CasesRequest, customers: list[Customer] | None
    ) -> tuple[list[Case], int]:
        """Get cases based on the provided filters."""
        return self.store.get_cases_by_customers_action_and_case_search(
            action=request.action,
            case_search=request.enquiry,
            customers=customers,
            offset=(request.page - 1) * request.page_size,
            limit=request.page_size,
        )
