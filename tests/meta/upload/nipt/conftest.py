import pytest
from sqlalchemy import update

from cg.apps.cgstats.db.models import Sample, Unaligned
from cg.apps.cgstats.stats import StatsAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Application


@pytest.fixture(name="nipt_upload_api_context")
def fixture_nipt_upload_api_context(
    cg_context: CGConfig, nipt_stats_api: StatsAPI, re_sequenced_sample_store: Store
) -> CGConfig:
    cg_context.status_db_ = re_sequenced_sample_store
    cg_context.cg_stats_api_ = nipt_stats_api

    return cg_context


@pytest.fixture(name="nipt_upload_api_failed_fc_context")
def fixture_nipt_upload_api_failed_fc_context(
    nipt_upload_api_context: CGConfig, sample_id: str
) -> CGConfig:
    nipt_upload_api_failed_fc_context: CGConfig = nipt_upload_api_context
    stats_api = nipt_upload_api_context.cg_stats_api
    status_db = nipt_upload_api_context.status_db
    stats_sample_id: int = (
        stats_api.Sample.query.filter(Sample.limsid == sample_id).first().sample_id
    )
    stats_api.session.execute(
        update(Unaligned).where(Unaligned.sample_id == stats_sample_id).values(readcounts=10)
    )
    stats_api.session.commit()
    application = status_db.get_sample_by_internal_id(
        internal_id=sample_id
    ).application_version.application
    status_db.session.execute(
        update(Application).where(Application.id == application.id).values({"target_reads": 20})
    )

    return nipt_upload_api_failed_fc_context
