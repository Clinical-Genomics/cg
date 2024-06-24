import pytest

from cg.models.fohm.reports import FohmReport


@pytest.fixture
def fohm_reports_raw() -> dict[str, str]:
    """Return raw FOHM reports."""
    return {
        "provnummer": "a_sample_number",
        "urvalskriterium": "a_selection_criteria",
        "GISAID_accession": "an_accession",
    }


@pytest.fixture
def fohm_report(fohm_reports_raw: list[dict]) -> FohmReport:
    """Return FohmReport."""
    return FohmReport.model_validate(fohm_reports_raw)


@pytest.fixture
def fohm_reports(fohm_report: FohmReport) -> list[FohmReport]:
    """Return FohmReports."""
    complementary_report = FohmReport.model_validate(
        {"provnummer": "1CS", "urvalskriterium": "criteria", "GISAID_accession": "an_accession"}
    )
    report_1 = FohmReport.model_validate(
        {
            "urvalskriterium": "criteria",
            "GISAID_accession": "an_accession",
            "provnummer": "44CS000000",
        }
    )
    return [fohm_report, complementary_report, report_1]
