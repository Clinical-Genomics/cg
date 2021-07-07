"""Fixtures for cli clean tests"""

import datetime
from pathlib import Path

import pytest
from cg.constants import Pipeline
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from tests.store_helpers import StoreHelpers


@pytest.fixture()
def clean_context(
    cg_context: CGConfig,
    helpers: StoreHelpers,
    project_dir: Path,
    timestamp_yesterday: datetime.datetime,
    timestamp_today: datetime.datetime,
) -> CGConfig:
    analysis_api = BalsamicAnalysisAPI(cg_context)
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
    cg_context.meta_apis["analysis_api"] = analysis_api

    cg_context.data_delivery.base_path = f"{project_dir}/rsync"

    return cg_context


@pytest.fixture(name="rsync_process")
def fixture_rsync_process(project_dir: Path) -> Path:
    """Return a rsync process after ensuing that is is created"""

    rsync_process = project_dir / "rsync" / "rsync_process"

    rsync_process.mkdir(exist_ok=True, parents=True)
    return rsync_process
