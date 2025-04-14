import pytest


@pytest.fixture
def microsalt_mwx_message(customer_id: str, ticket_id: str) -> str:
    """Return the delivery message for a microSALT MWX case."""
    return (
        f"Hello,\n\n"
        f"The analysis is now complete and the fastq files are being uploaded to:\n\n"
        f"/home/{customer_id}/inbox/{ticket_id} \n\n"
        "The QC report can be found attached."
    )


@pytest.fixture
def microsalt_mwr_message(customer_id: str, ticket_id: str) -> str:
    """Return the delivery message for a microSALT MWX case."""
    return (
        f"Hello,\n\n"
        f"The analysis is now complete and the fastq files are being uploaded to:\n\n"
        f"/home/{customer_id}/inbox/{ticket_id} \n\n"
        "The QC and Typing reports can be found attached."
    )
