import pytest

from cg.meta.upload.gisaid import GisaidAPI
from cg.models.cg_config import CGConfig
from cg.models.gisaid.reports import GisaidComplementaryReport


@pytest.fixture
def gisaid_log_raw() -> list[dict[str, str]]:
    """Return a raw GISAID log."""
    return [
        {"code": "epi_isl_id", "msg": "hCoV-19/Sweden/01_SE100_00CS100000/2024; EPI_ISL_00000000"},
    ]


@pytest.fixture
def gisaid_complementary_report_raw() -> dict[str, str]:
    """Return a raw GISAID complementary report."""
    return {
        "provnummer": "a_sample_number",
        "urvalskriterium": "a_selection_criteria",
    }


@pytest.fixture
def gisaid_complementary_report(
    gisaid_complementary_report_raw: list[dict],
) -> GisaidComplementaryReport:
    """Return GisaidComplementaryReport."""
    return GisaidComplementaryReport.model_validate(gisaid_complementary_report_raw)


@pytest.fixture
def gisaid_complementary_reports(
    gisaid_complementary_report: GisaidComplementaryReport,
) -> list[GisaidComplementaryReport]:
    """Return GISAID complementary reports."""
    report_1 = GisaidComplementaryReport.model_validate(
        {"provnummer": "1CS", "urvalskriterium": "criteria", "GISAID_accession": "an_accession"}
    )
    complementary_report = GisaidComplementaryReport.model_validate(
        {
            "urvalskriterium": "criteria",
            "provnummer": "44CS000000",
        }
    )
    return [gisaid_complementary_report, complementary_report, report_1]


@pytest.fixture
def gisaid_api(
    cg_context: CGConfig,
) -> GisaidAPI:
    """GISAID API fixture."""
    return GisaidAPI(cg_context)
