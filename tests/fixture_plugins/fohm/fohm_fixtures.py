import pytest

from cg.models.fohm.reports import FohmComplementaryReport


@pytest.fixture
def fohm_complementary_report_raw() -> dict[str, str]:
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
    return FohmComplementaryReport.model_validate(fohm_complementary_report_raw)


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


@pytest.fixture
def fohm_pangolin_report_raw() -> dict[str, str]:
    """Return FOHM Pangolin report."""
    return {
        "taxon": "a_taxon",
        "lineage": "a_lineage",
        "conflict": "a_conflict",
        "ambiguity_score": "an_ambiguity_score",
        "scorpio_call": "a_scorpio_call",
        "scorpio_support": "a_scorpio_support",
        "scorpio_conflict": "a_scorpio_conflict",
        "scorpio_notes": "a_scorpio_note",
        "version": "a_version",
        "pangolin_version": "a_pangolin_version",
        "scorpio_version": "a_wcorpio_version",
        "constellation_version": "a_constellation_vversion",
        "is_designated": "a_designation",
        "qc_status": "a_qc_status",
        "qc_notes": "a_qc_note",
        "note": "a_note",
    }
