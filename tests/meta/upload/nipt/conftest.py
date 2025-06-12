import pytest
from sqlalchemy import update

from cg.models.cg_config import CGConfig
from cg.store.store import Store


@pytest.fixture
def nipt_upload_api_context(
    cg_context: CGConfig, re_sequenced_sample_illumina_data_store: Store
) -> CGConfig:
    cg_context.status_db_ = re_sequenced_sample_illumina_data_store
    return cg_context


@pytest.fixture
def nipt_upload_api_failed_fc_context(
    nipt_upload_api_context: CGConfig,
    case_id_for_sample_on_multiple_flow_cells: str,
    re_sequenced_sample_illumina_data_store: Store,
) -> CGConfig:
    nipt_upload_api_failed_fc_context: CGConfig = nipt_upload_api_context
    nipt_upload_api_failed_fc_context.status_db_ = re_sequenced_sample_illumina_data_store
    status_db = nipt_upload_api_context.status_db

    application = status_db.get_application_by_case(case_id_for_sample_on_multiple_flow_cells)
    application.target_reads: int = 1_000_000_000_000

    return nipt_upload_api_failed_fc_context
