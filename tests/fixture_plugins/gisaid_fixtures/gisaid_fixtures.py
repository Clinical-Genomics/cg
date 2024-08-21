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
def gisaid_sars_cov_complementary_report_complete_raw(
    sars_cov_sample_number: str,
) -> dict[str, str]:
    """Return a raw GISAID complementary report."""
    return {
        "GISAID_accession": "an_accession",
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
    gisaid_sars_cov_complementary_report_complete_raw: dict[str, str],
) -> list[GisaidComplementaryReport]:
    """Return GISAID complementary reports."""
    sars_cov_complementary_report_complete = GisaidComplementaryReport.model_validate(
        gisaid_sars_cov_complementary_report_complete_raw
    )
    sars_cov_complementary_report = GisaidComplementaryReport.model_validate(
        gisaid_sars_cov_complementary_report_raw
    )
    return [
        gisaid_complementary_report,
        sars_cov_complementary_report,
        sars_cov_complementary_report_complete,
    ]


@pytest.fixture
def gisaid_api(
    cg_context: CGConfig,
) -> GisaidAPI:
    """GISAID API fixture."""
    return GisaidAPI(cg_context)


@pytest.fixture
def gisaid_samples_raw() -> dict[str, str]:
    """Return a raw GISAID sample."""
    return {
        "case_id": "a_case_id",
        "cg_lims_id": "a_cg_lims_id",
        "covv_authors": "a_covv_authors",
        "covv_collection_date": "2000-01-01",
        "covv_gender": "unknown",
        "covv_host": "Human",
        "covv_passage": "Original",
        "covv_patient_age": "unknown",
        "covv_patient_status": "unknown",
        "covv_subm_lab": "Karolinska University Hospital",
        "covv_subm_lab_addr": "171 76 Stockholm, Sweden",
        "covv_type": "betacoronavirus",
        "fn": "a_fn",
        "region": "a_region",
        "region_code": "a_region_code",
        "submitter": "a_submitter",
    }
