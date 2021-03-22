"""Fixtures for cli clean tests"""

from pathlib import Path

import pytest

from cg.constants import Pipeline
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI


@pytest.fixture()
def clean_context(context_config, helpers, timestamp_yesterday, timestamp_today):
    analysis_api = BalsamicAnalysisAPI(context_config)
    store = analysis_api.status_db

    # Create textbook case for cleaning
    case_to_clean = helpers.add_case(
        store=store, internal_id="balsamic_case_clean", case_id="balsamic_case_clean"
    )
    sample_case_to_clean = helpers.add_sample(
        store,
        internal_id="balsamic_sample_clean",
        is_tumour=True,
        application_type="wgs",
        data_analysis=Pipeline.BALSAMIC,
    )
    helpers.add_relationship(store, case=case_to_clean, sample=sample_case_to_clean)

    helpers.add_analysis(
        store,
        case=case_to_clean,
        pipeline=Pipeline.BALSAMIC,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    Path(analysis_api.get_case_path("balsamic_case_clean")).mkdir(exist_ok=True, parents=True)

    # Create textbook case not for cleaning
    case_to_not_clean = helpers.add_case(
        store=store, internal_id="balsamic_case_not_clean", case_id="balsamic_case_not_clean"
    )
    case_to_not_clean.action = "running"
    store.commit()

    sample_case_to_not_clean = helpers.add_sample(
        store,
        internal_id="balsamic_sample_not_clean",
        is_tumour=True,
        application_type="wgs",
        data_analysis="balsamic",
    )
    helpers.add_relationship(store, case=case_to_not_clean, sample=sample_case_to_not_clean)

    helpers.add_analysis(
        store,
        case=case_to_not_clean,
        pipeline="balsamic",
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
    )
    Path(analysis_api.get_case_path("balsamic_case_not_clean")).mkdir(exist_ok=True, parents=True)
    context_config["analysis_api"] = analysis_api
    return context_config
