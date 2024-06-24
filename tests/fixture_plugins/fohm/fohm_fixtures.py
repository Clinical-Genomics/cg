import pytest


@pytest.fixture
def fohm_reports_raw() -> dict[str, str]:
    """Return raw FOHM reports."""
    return {
        "provnummer": "a_sample_number",
        "urvalskriterium": "a_selection_criteria",
        "GISAID_accession": "an_accession",
    }
