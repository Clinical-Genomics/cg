"""Delivery report API fixtures."""

import pytest

from cg.meta.delivery_report.raredisease import RarediseaseDeliveryReportAPI
from cg.meta.delivery_report.rnafusion import RnafusionDeliveryReportAPI
from cg.models.cg_config import CGConfig
from cg.models.delivery_report.report import ScoutVariantsFiles


@pytest.fixture
def raredisease_delivery_report_api(
    raredisease_delivery_report_context: CGConfig,
) -> RarediseaseDeliveryReportAPI:
    return RarediseaseDeliveryReportAPI(
        analysis_api=raredisease_delivery_report_context.meta_apis["analysis_api"]
    )


@pytest.fixture
def rnafusion_delivery_report_api(
    rnafusion_delivery_report_context: CGConfig,
) -> RnafusionDeliveryReportAPI:
    return RnafusionDeliveryReportAPI(
        analysis_api=rnafusion_delivery_report_context.meta_apis["analysis_api"]
    )


@pytest.fixture
def scout_variants_files(snv_vcf_file: str, sv_vcf_file: str) -> ScoutVariantsFiles:
    return ScoutVariantsFiles(snv_vcf=snv_vcf_file, sv_vcf=sv_vcf_file)
