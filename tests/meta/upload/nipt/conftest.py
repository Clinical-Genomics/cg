import pytest
from sqlalchemy import update

from cg.models.cg_config import CGConfig
from cg.store.models import Application
from cg.store.store import Store
from tests.store.api.conftest import store_failing_sequencing_qc
from tests.store.crud.conftest import re_sequenced_sample_store


@pytest.fixture
def nipt_upload_api_context(cg_context: CGConfig, re_sequenced_sample_store: Store) -> CGConfig:
    cg_context.status_db_ = re_sequenced_sample_store

    return cg_context


@pytest.fixture
def nipt_upload_api_failed_fc_context(
    nipt_upload_api_context: CGConfig, sample_id: str, store_failing_sequencing_qc: Store
) -> CGConfig:
    nipt_upload_api_failed_fc_context: CGConfig = nipt_upload_api_context
    nipt_upload_api_failed_fc_context.status_db_ = store_failing_sequencing_qc
    status_db = nipt_upload_api_context.status_db

    application = status_db.get_sample_by_internal_id(
        internal_id=sample_id
    ).application_version.application
    status_db.session.execute(
        update(Application).where(Application.id == application.id).values({"target_reads": 20})
    )

    return nipt_upload_api_failed_fc_context
