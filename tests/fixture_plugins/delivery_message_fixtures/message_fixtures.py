import pytest


@pytest.fixture
def analysis_scout_message(mip_case_id: str, customer_id: str, ticket_id: str) -> str:
    """Return the delivery message for a MIP case."""
    return (
        "Hello,\n\n"
        "The analysis has been uploaded to Scout for the following case:\n\n"
        f"https://scout.scilifelab.se/{customer_id}/{mip_case_id}\n\n"
        "The analysis files are currently being uploaded to your inbox on Caesar:\n\n"
        f"/home/{customer_id}/inbox/{ticket_id}"
    )


@pytest.fixture
def microsalt_mwx_message(customer_id: str, ticket_id: str) -> str:
    """Return the delivery message for a microSALT MWX case."""
    return (
        "Hello,\n\n"
        "The analysis is now complete and the fastq files are being uploaded to:\n\n"
        f"/home/{customer_id}/inbox/{ticket_id} \n\n"
        "The QC report can be found attached."
    )


@pytest.fixture
def microsalt_mwr_message(customer_id: str, ticket_id: str) -> str:
    """Return the delivery message for a microSALT MWX case."""
    return (
        "Hello,\n\n"
        "The analysis is now complete and the fastq files are being uploaded to:\n\n"
        f"/home/{customer_id}/inbox/{ticket_id} \n\n"
        "The QC and Typing reports can be found attached."
    )


@pytest.fixture
def nallo_raw_data_analysis_message(customer_id: str, nallo_case_id: str, ticket_id: str) -> str:
    """Return the delivery message for case with raw-data and analysis delivery."""
    return (
        "Hello,\n\n"
        "The raw data and analysis files for the following case are currently being "
        "uploaded to your inbox on Caesar:\n\n"
        f"{nallo_case_id}\n\n"
        "Available under: \n"
        f"/home/{customer_id}/inbox/{ticket_id}"
    )


@pytest.fixture
def nallo_raw_data_analysis_scout_message(
    customer_id: str, nallo_case_id: str, ticket_id: str
) -> str:
    """Return the delivery message for a Nallo case with raw-data, analysis and Scout delivery."""
    return (
        "Hello,\n\n"
        "The analysis has been uploaded to Scout for the following case:\n\n"
        f"https://scout38.scilifelab.se/{customer_id}/{nallo_case_id}\n\n"
        "The raw data and analysis files are currently being uploaded to your inbox on Caesar:\n\n"
        f"/home/{customer_id}/inbox/{ticket_id}"
    )


@pytest.fixture
def nallo_raw_data_scout_message(customer_id: str, nallo_case_id: str, ticket_id: str) -> str:
    """Return the delivery message for a Nallo case with Scout delivery."""
    return (
        "Hello,\n\n"
        "The analysis has been uploaded to Scout for the following case:\n\n"
        f"https://scout38.scilifelab.se/{customer_id}/{nallo_case_id}\n\n"
        "The raw data files are currently being uploaded to your inbox on Caesar:\n\n"
        f"/home/{customer_id}/inbox/{ticket_id}"
    )


@pytest.fixture
def statina_message(customer_id: str, ticket_id: str) -> str:
    """Return the delivery message for a fluffy case."""
    return (
        "Hello,\n\n"
        "Batch 1 is now available in Statina.\n\n"
        "https://statina.clinicalgenomics.se/batches/1"
    )
