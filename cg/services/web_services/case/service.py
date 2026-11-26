from cg.server.dto.cases.requests import CasesRequest
from cg.services import cancellation_service
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

    def cancel_cases(self, entry_ids: list[str], user_email: str) -> str:
        case_ids: set[str] = {
            self.store.get_case_by_entry_id(entry_id).internal_id for entry_id in entry_ids
        }
        try:
            cancellation_service.cases(
                case_ids=case_ids,
                comment="Cancelled in admin view",
                user=user_email,
                status_db=self.store,
            )
            self.store.commit_to_store()
        except Exception:
            self.store.rollback()
            raise
        return f"Cancelled cases: {', '.join(sorted(case_ids))}"
