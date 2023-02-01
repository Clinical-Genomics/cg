import pytest
from sqlalchemy import update

from cg.apps.cgstats.db import models as stats_models
from cg.apps.cgstats.stats import StatsAPI
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from tests.apps.cgstats.conftest import fixture_nipt_stats_api, fixture_stats_api
from tests.store.api.conftest import fixture_re_sequenced_sample_store


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
        stats_api.Sample.query.filter(stats_models.Sample.limsid == sample_id).first().sample_id
    )
    stats_api.session.execute(
        update(stats_models.Unaligned)
        .where(stats_models.Unaligned.sample_id == stats_sample_id)
        .values(readcounts=10)
    )
    stats_api.session.commit()
    application = (
        status_db.Sample.query.filter(models.Sample.internal_id == sample_id)
        .first()
        .application_version.application
    )
    status_db.session.execute(
        update(models.Application)
        .where(models.Application.id == application.id)
        .values({"target_reads": 20})
    )

    return nipt_upload_api_failed_fc_context
