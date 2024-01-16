from cg.store.models import Case


def get_fastq_delivery_path(case: Case) -> str:
    ticket_id: str = case.latest_ticket
    customer_id: str = case.customer.internal_id
    return f"/home/{customer_id}/inbox/{ticket_id}"
