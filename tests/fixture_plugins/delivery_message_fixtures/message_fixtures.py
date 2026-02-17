from string import Template

import pytest

from cg.services.delivery_message.messages.utils import REMINDER_TO_DOWNLOAD_MESSAGE


@pytest.fixture
def analysis_scout_message(mip_case_id: str, customer_id: str, ticket_id: str) -> str:
    """Return the delivery message for a MIP case."""
    return (
        "Hello,\n\n"
        "The analysis has been uploaded to Scout for the following case:\n\n"
        f"https://scout.scilifelab.se/{customer_id}/{mip_case_id}\n\n"
        "The analysis files are currently being uploaded to your inbox on Caesar:\n\n"
        f"/home/{customer_id}/inbox/{ticket_id} \n\n"
        f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
    )


@pytest.fixture
def microsalt_message(customer_id: str, ticket_id: str) -> str:
    """Return the delivery message for a microSALT case."""
    return (
        "Hello,\n\n"
        "The analysis is now complete and the fastq files are being uploaded to:\n\n"
        f"/home/{customer_id}/inbox/{ticket_id} \n\n"
        "The QC and Typing reports can be found attached. \n\n"
        f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
    )


@pytest.fixture
def raw_data_analysis_message() -> Template:
    """Return the delivery message template for a case with raw-data and analysis delivery."""

    return Template(
        "Hello,\n\n"
        "The raw data and analysis files for the following case are currently being "
        "uploaded to your inbox on Caesar:\n\n"
        "$case_id\n\n"
        "Available under: \n"
        "/home/$customer_id/inbox/$ticket_id \n\n"
        f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
    )


@pytest.fixture
def raw_data_analysis_scout38_message() -> Template:
    """Return the delivery message template for a scout38 case with raw-data, analysis and Scout delivery."""
    return Template(
        "Hello,\n\n"
        "The analysis has been uploaded to Scout for the following case:\n\n"
        "https://scout38.sys.scilifelab.se/$customer_id/case_id\n\n"
        "The raw data and analysis files are currently being uploaded to your inbox on Caesar:\n\n"
        "/home/$customer_id/inbox/$ticket_id \n\n"
        f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
    )


@pytest.fixture
def raw_data_scout38_message() -> Template:
    """Return the delivery message template for a scout38 case with Scout delivery."""
    return Template(
        "Hello,\n\n"
        "The analysis has been uploaded to Scout for the following case:\n\n"
        "https://scout38.sys.scilifelab.se/$customer_id/case_id\n\n"
        "The raw data files are currently being uploaded to your inbox on Caesar:\n\n"
        "/home/$customer_id/inbox/$ticket_id \n\n"
        f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
    )


@pytest.fixture
def statina_message(customer_id: str, ticket_id: str) -> str:
    """Return the delivery message for a fluffy case."""
    return (
        "Hello,\n\n"
        "Batch 1 is now available in Statina.\n\n"
        "https://statina.clinicalgenomics.se/batches/1"
    )
