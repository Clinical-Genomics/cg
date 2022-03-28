import pytest

import datetime as dt

from cgmodels.cg.constants import Pipeline

from cg.meta.workflow.fastq import FastqAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import models
from tests.store_helpers import StoreHelpers


@pytest.fixture(name="fastq_context")
def fixture_fastq_context(
    cg_context: CGConfig,
    fastq_case,
    helpers: StoreHelpers,
    case_id,
    tb_api,
) -> CGConfig:
    """Returns a CGConfig where the meta_apis["analysis_api"] is a FastqAnalysisAPI and a store
    containing a fastq case"""
    _store = cg_context.status_db
    cg_context.trailblazer_api_ = tb_api
    fastq_analysis = FastqAnalysisAPI(config=cg_context, pipeline=Pipeline.FASTQ)

    # Add fastq case to db
    fastq_case["samples"][0]["sequenced_at"] = dt.datetime.now()
    helpers.ensure_case_from_dict(store=_store, case_info=fastq_case)

    cg_context.meta_apis["analysis_api"] = fastq_analysis
    return cg_context


@pytest.fixture(name="fastq_case")
def fixture_fastq_case(case_id, family_name, sample_id, cust_sample_id, ticket_nr) -> dict:
    """Returns a dict describing a fastq case"""
    return {
        "name": family_name,
        "panels": None,
        "internal_id": case_id,
        "data_analysis": "fastq",
        "data_deliver": "fastq",
        "completed_at": None,
        "action": None,
        "samples": [
            {
                "internal_id": sample_id,
                "sex": "male",
                "name": cust_sample_id,
                "ticket_number": ticket_nr,
                "reads": 1000000,
                "capture_kit": "anything",
            },
        ],
    }
