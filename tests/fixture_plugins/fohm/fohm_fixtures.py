import pytest

from cg.models.fohm.reports import FohmComplementaryReport


@pytest.fixture
def fohm_complementary_reports_raw() -> dict[str, str]:
    """Return raw FOHM complementary reports."""
    return {
        "provnummer": "a_sample_number",
        "urvalskriterium": "a_selection_criteria",
        "GISAID_accession": "an_accession",
    }


@pytest.fixture
def fohm_complementary_report(
    fohm_complementary_reports_raw: list[dict],
) -> FohmComplementaryReport:
    """Return FohmComplementaryReport."""
    return FohmComplementaryReport.model_validate(fohm_complementary_reports_raw)


@pytest.fixture
def fohm_complementary_reports(
    fohm_complementary_report: FohmComplementaryReport,
) -> list[FohmComplementaryReport]:
    """Return FOHM complementary reports."""
    report_1 = FohmComplementaryReport.model_validate(
        {"provnummer": "1CS", "urvalskriterium": "criteria", "GISAID_accession": "an_accession"}
    )
    complementary_report = FohmComplementaryReport.model_validate(
        {
            "urvalskriterium": "criteria",
            "GISAID_accession": "an_accession",
            "provnummer": "44CS000000",
        }
    )
    return [fohm_complementary_report, complementary_report, report_1]
