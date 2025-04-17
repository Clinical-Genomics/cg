from cg.constants import Workflow
from cg.store.models import Case


def get_caesar_delivery_path(case: Case) -> str:
    ticket_id: str = case.latest_ticket
    customer_id: str = case.customer.internal_id
    return f"/home/{customer_id}/inbox/{ticket_id}"


def get_scout_link(case: Case) -> str:
    customer_id: str = case.customer.internal_id
    case_name: str = case.name
    url: str = (
        "https://scout38.sys.scilifelab.se/"
        if case.data_analysis == Workflow.NALLO
        else "https://scout.scilifelab.se/"
    )
    return f"{url}{customer_id}/{case_name}"


def get_scout_links_row_separated(cases: list[Case]) -> str:
    scout_links: list[str] = [get_scout_link(case) for case in cases]
    return "\n".join(scout_links)


def get_pangolin_delivery_path(case: Case) -> str:
    customer_id: str = case.customer.internal_id
    return f"/home/{customer_id}/inbox/wwLab_automatisk_hamtning"


def get_batch_id_for_case(case: Case) -> str:
    return case.name.split("-")[1]


def get_statina_link(batch_id: str) -> str:
    return f"https://statina.clinicalgenomics.se/batches/{batch_id}"
