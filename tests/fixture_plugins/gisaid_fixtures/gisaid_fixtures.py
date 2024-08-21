import pytest

from cg.meta.upload.gisaid import GisaidAPI
from cg.models.cg_config import CGConfig
from cg.models.gisaid.reports import GisaidComplementaryReport


@pytest.fixture
def gisaid_log_raw(sars_cov_sample_number: str) -> list[dict[str, str]]:
    """Return a raw GISAID log."""
    return [
        {
            "code": "epi_isl_id",
            "msg": f"hCoV-19/Sweden/01_SE100_{sars_cov_sample_number}/2024; EPI_ISL_00000000",
        },
    ]


@pytest.fixture
def gisaid_complementary_report_raw() -> dict[str, str]:
    """Return a raw GISAID complementary report."""
    return {
        "provnummer": "a_sample_number",
        "urvalskriterium": "a_selection_criteria",
    }


@pytest.fixture
def gisaid_sars_cov_complementary_report_raw(sars_cov_sample_number: str) -> dict[str, str]:
    """Return a raw GISAID complementary report."""
    return {
        "urvalskriterium": "criteria",
        "provnummer": f"{sars_cov_sample_number}",
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
    gisaid_sars_cov_complementary_report_raw: dict[str, str],
) -> list[GisaidComplementaryReport]:
    """Return GISAID complementary reports."""
    report_1 = GisaidComplementaryReport.model_validate(
        {"provnummer": "1CS", "urvalskriterium": "criteria", "GISAID_accession": "an_accession"}
    )
    sars_cov_complementary_report = GisaidComplementaryReport.model_validate(
        gisaid_sars_cov_complementary_report_raw
    )
    return [gisaid_complementary_report, sars_cov_complementary_report, report_1]


@pytest.fixture
def gisaid_api(
    cg_context: CGConfig,
) -> GisaidAPI:
    """GISAID API fixture."""
    return GisaidAPI(cg_context)
