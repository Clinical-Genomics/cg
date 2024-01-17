from cg.store.models import Case


def get_fastq_delivery_path(case: Case) -> str:
    ticket_id: str = case.latest_ticket
    customer_id: str = case.customer.internal_id
    return f"/home/{customer_id}/inbox/{ticket_id}"


def get_scout_link(case: Case) -> str:
    customer_id: str = case.customer.internal_id
    case_name: str = case.name
    return f"https://scout.scilifelab.se/{customer_id}/{case_name}"


def get_pangolin_delivery_path(case: Case) -> str:
    customer_id: str = case.customer.internal_id
    return f"/home/{customer_id}/inbox/wwLab_automatisk_hamtning"


def get_statina_link(case: Case) -> str:
    batch_id: str = case.name.split("-")[1]
    return f"https://statina.clinicalgenomics.se/batches/{batch_id}"
