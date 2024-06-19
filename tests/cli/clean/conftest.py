"""Fixtures for cli clean tests"""

import datetime
from pathlib import Path

import pytest

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Workflow
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.store import Store
from tests.meta.clean.conftest import (
    hk_flow_cell_to_clean_bundle,
    hk_sample_bundle_for_flow_cell_to_clean,
    housekeeper_api_with_flow_cell_to_clean,
    store_with_flow_cell_to_clean,
    tmp_flow_cell_not_to_clean_path,
    tmp_flow_cell_to_clean,
    tmp_flow_cell_to_clean_path,
    tmp_sample_sheet_clean_flow_cell_path,
)
from tests.store_helpers import StoreHelpers


@pytest.fixture
def balsamic_case_clean() -> str:
    """Return a balsamic case to clean"""
    return "balsamic_case_clean"


@pytest.fixture
def balsamic_case_not_clean() -> str:
    """Return a balsamic case to clean"""
    return "balsamic_case_not_clean"


@pytest.fixture
def clean_context(
    balsamic_case_clean: str,
    balsamic_case_not_clean: str,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    project_dir: Path,
    timestamp_yesterday: datetime.datetime,
) -> CGConfig:
    analysis_api = BalsamicAnalysisAPI(cg_context)
    store = analysis_api.status_db

    # Create textbook case for cleaning
    case_to_clean = helpers.add_case(
        store=store,
        internal_id=balsamic_case_clean,
        name=balsamic_case_clean,
        data_analysis=Workflow.BALSAMIC,
    )
    sample_case_to_clean = helpers.add_sample(
        store, application_type="wgs", is_tumour=True, internal_id=balsamic_case_clean
    )
    helpers.add_relationship(store, case=case_to_clean, sample=sample_case_to_clean)

    helpers.add_analysis(
        store,
        case=case_to_clean,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
        workflow=Workflow.BALSAMIC,
    )
    Path(analysis_api.get_case_path(balsamic_case_clean)).mkdir(exist_ok=True, parents=True)

    # Create textbook case not for cleaning
    case_to_not_clean = helpers.add_case(
        store=store,
        internal_id=balsamic_case_not_clean,
        name=balsamic_case_not_clean,
        data_analysis=Workflow.BALSAMIC,
    )
    case_to_not_clean.action = "running"
    store.session.commit()

    sample_case_to_not_clean = helpers.add_sample(
        store, application_type="wgs", is_tumour=True, internal_id=balsamic_case_not_clean
    )
    helpers.add_relationship(store, case=case_to_not_clean, sample=sample_case_to_not_clean)

    helpers.add_analysis(
        store,
        case=case_to_not_clean,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
        workflow=Workflow.BALSAMIC,
    )
    Path(analysis_api.get_case_path(balsamic_case_not_clean)).mkdir(exist_ok=True, parents=True)
    cg_context.meta_apis["analysis_api"] = analysis_api

    cg_context.data_delivery.base_path = f"{project_dir}/rsync"

    return cg_context


@pytest.fixture
def rsync_process(project_dir: Path) -> Path:
    """Return a rsync process after ensuing that is is created"""

    rsync_process = project_dir / "rsync" / "rsync_process"

    rsync_process.mkdir(exist_ok=True, parents=True)
    return rsync_process


@pytest.fixture
def microsalt_case_clean_dry() -> str:
    """Return a microsalt case to clean in dry-run"""
    return "microsalt_case_clean_dry"


@pytest.fixture
def microsalt_case_clean() -> str:
    """Return a microsalt case to clean"""
    return "microsalt_case_clean"


@pytest.fixture(scope="function")
def clean_context_microsalt(
    microsalt_case_clean: str,
    microsalt_case_clean_dry: str,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    project_dir: Path,
    timestamp_yesterday: datetime.datetime,
    timestamp_now: datetime.datetime,
    mocker,
) -> CGConfig:
    """Clean context for microsalt."""

    analysis_api = MicrosaltAnalysisAPI(cg_context)
    store = analysis_api.status_db

    mocker.patch.object(MicrosaltAnalysisAPI, "get_case_path")

    # Create textbook case for cleaning
    MicrosaltAnalysisAPI.get_case_path.return_value = [
        Path(analysis_api.root_dir, microsalt_case_clean)
    ]

    case_to_clean = helpers.add_case(
        store=store,
        internal_id=microsalt_case_clean,
        name=microsalt_case_clean,
        data_analysis=Workflow.MICROSALT,
    )
    sample_case_to_clean = helpers.add_sample(store, internal_id=microsalt_case_clean)

    helpers.add_relationship(store, case=case_to_clean, sample=sample_case_to_clean)

    helpers.add_analysis(
        store,
        case=case_to_clean,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
        workflow=Workflow.MICROSALT,
    )
    case_path_list = analysis_api.get_case_path(microsalt_case_clean)
    for path in case_path_list:
        Path(path).mkdir(exist_ok=True, parents=True)

    # Create textbook case for cleaning in dry run
    MicrosaltAnalysisAPI.get_case_path.return_value = [
        Path(analysis_api.root_dir, microsalt_case_clean_dry)
    ]

    case_to_clean_dry_run = helpers.add_case(
        store=store,
        internal_id=microsalt_case_clean_dry,
        name=microsalt_case_clean_dry,
        data_analysis=Workflow.MICROSALT,
    )

    sample_case_to_not_clean = helpers.add_sample(store, internal_id=microsalt_case_clean_dry)
    helpers.add_relationship(store, case=case_to_clean_dry_run, sample=sample_case_to_not_clean)

    helpers.add_analysis(
        store,
        case=case_to_clean_dry_run,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        cleaned_at=None,
        workflow=Workflow.MICROSALT,
    )

    case_path_list = analysis_api.get_case_path(microsalt_case_clean_dry)
    for path in case_path_list:
        Path(path).mkdir(exist_ok=True, parents=True)

    cg_context.meta_apis["analysis_api"] = analysis_api

    cg_context.data_delivery.base_path = f"{project_dir}/rsync"

    return cg_context


@pytest.fixture(scope="function")
def clean_flow_cells_context(
    cg_context: CGConfig,
    tmp_illumina_sequencing_runs_directory,
    tmp_illumina_demultiplexed_flow_cells_directory,
    store_with_flow_cell_to_clean: Store,
    housekeeper_api_with_flow_cell_to_clean: HousekeeperAPI,
) -> CGConfig:
    cg_context.run_instruments.illumina.sequencing_runs_dir = tmp_illumina_sequencing_runs_directory
    cg_context.run_instruments.illumina.demultiplexed_runs_dir = (
        tmp_illumina_demultiplexed_flow_cells_directory
    )
    cg_context.housekeeper_api_ = housekeeper_api_with_flow_cell_to_clean
    cg_context.status_db_ = store_with_flow_cell_to_clean

    return cg_context
