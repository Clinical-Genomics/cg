"""Test CG CLI upload module."""
import logging
from datetime import datetime, timedelta

from _pytest.logging import LogCaptureFixture
from cgmodels.cg.constants import Pipeline
from click.testing import CliRunner

from cg.cli.upload.base import upload
from cg.constants import DataDelivery
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from tests.cli.workflow.rnafusion.conftest import fixture_rnafusion_case_id
from tests.store_helpers import StoreHelpers


def test_upload_started_long_time_ago_raises_exception(
    cli_runner: CliRunner,
    base_context: CGConfig,
    helpers: StoreHelpers,
):
    """Test that an upload for a missing case does fail hard."""

    # GIVEN an analysis that is already uploading since a week ago
    disk_store: Store = base_context.status_db
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    today = datetime.now()
    upload_started = today - timedelta(hours=100)
    helpers.add_analysis(disk_store, case=case, uploading=True, upload_started=upload_started)

    # WHEN trying to upload an analysis that was started a long time ago
    result = cli_runner.invoke(upload, ["-f", case_id], obj=base_context)

    # THEN an exception should have be thrown
    assert result.exit_code != 0
    assert result.exception


def test_upload_force_restart(
    cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers, caplog: LogCaptureFixture
):
    """Test that a case that is already uploading can be force restarted."""
    caplog.set_level(logging.INFO)

    # GIVEN an analysis that is already uploading
    disk_store: Store = base_context.status_db
    case: models.Family = helpers.add_case(disk_store)
    case_id: str = case.internal_id

    helpers.add_analysis(disk_store, case=case, uploading=True)

    # WHEN trying to upload it again with the force restart flag
    result = cli_runner.invoke(upload, ["-f", case_id, "-r"], obj=base_context)

    # THEN it tries to restart the upload
    assert "already started" not in result.output


def test_upload_rnafusion(
    cli_runner: CliRunner,
    base_context: CGConfig,
    helpers: StoreHelpers,
    caplog: LogCaptureFixture,
    case_id: str = fixture_rnafusion_case_id,
):
    """Test that a case that is already uploading can be force restarted."""
    caplog.set_level(logging.INFO)

    # GIVEN an analysis that is already uploading
    disk_store: Store = base_context.status_db
    case: models.Family = helpers.add_case(
        store=disk_store,
        data_analysis=Pipeline.RNAFUSION,
    )
    # case_id: str = case.internal_id

    helpers.add_analysis(
        disk_store,
        case=case,
        pipeline=Pipeline.RNAFUSION,
        data_delivery=DataDelivery.SCOUT,
        completed_at=datetime.now(),
    )

    # WHEN trying to upload
    result = cli_runner.invoke(upload, ["-f", case_id], obj=base_context, catch_exceptions=True)
    a = result.output
    # THEN it tries to restart the upload    assert "already started" not in result.output

    assert "already started" not in result.output
