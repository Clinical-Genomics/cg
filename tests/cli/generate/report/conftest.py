from datetime import datetime

import click
import pytest

from cg.cli.generate.report.base import generate_delivery_report
from cg.constants import Workflow
from cg.models.cg_config import CGConfig
from tests.mocks.report import MockMipDNAAnalysisAPI, MockMipDNAReportAPI


@pytest.fixture
def mip_dna_context(cg_context, helpers, case_id, real_housekeeper_api) -> CGConfig:
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
        prep_category="wgs",
    )
    case = helpers.add_case(
        store=store,
        data_analysis=Workflow.MIP_DNA,
        internal_id=case_id,
    )
    sample = helpers.add_sample(
        store=store, application_tag="WGSA", application_type="wgs", customer_id="cust000"
    )
    helpers.add_analysis(
        store=store,
        case=case,
        started_at=datetime.now(),
        delivery_reported_at=datetime.now(),
        workflow=Workflow.MIP_DNA,
    )
    helpers.add_relationship(
        store=store,
        sample=sample,
        case=case,
        status="affected",
    )

    return cg_context


@pytest.fixture
def delivery_report_click_context(mip_dna_context) -> click.Context:
    """Click delivery report context fixture"""

    return click.Context(generate_delivery_report, obj=mip_dna_context)
