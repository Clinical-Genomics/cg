from datetime import datetime

import pytest
from cgmodels.cg.constants import Pipeline
from cg.models.cg_config import CGConfig
from tests.mocks.report import MockMipDNAReportAPI, MockMipDNAAnalysisAPI


@pytest.fixture(name="mip_dna_context")
def fixture_mip_dna_context(cg_context, helpers, case_id, real_housekeeper_api) -> CGConfig:
    """MIP DNA context fixture"""

    store = cg_context.status_db
    cg_context.housekeeper_api_ = real_housekeeper_api
    cg_context.meta_apis["report_api"] = MockMipDNAReportAPI(
        cg_context, MockMipDNAAnalysisAPI(config=cg_context)
    )

    # Add app tag, case, sample, analysis and relationships to DB
    helpers.ensure_application_version(
        store=store,
        application_tag="WGSA",
        application_type="wgs",
    )
    case = helpers.add_case(
        store=store,
        data_analysis=Pipeline.MIP_DNA,
        internal_id=case_id,
    )
    sample = helpers.add_sample(
        store=store,
        customer_id="cust000",
        application_tag="WGSA",
        application_type="wgs",
    )
    helpers.add_analysis(
        store=store,
        case=case,
        pipeline=Pipeline.MIP_DNA,
        started_at=datetime.now(),
    )
    helpers.add_relationship(
        store=store,
        sample=sample,
        case=case,
        status="affected",
    )

    return cg_context
