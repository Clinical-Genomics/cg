"""Test CG CLI upload module."""

from datetime import datetime, timedelta
from unittest.mock import ANY, Mock, create_autospec

from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

from cg.cli.upload import base
from cg.cli.upload.base import upload
from cg.constants.constants import DataDelivery, Workflow
from cg.constants.process import EXIT_SUCCESS
from cg.meta.upload.raw_data.raw_data_upload_api import RawDataUploadAPI
from cg.models.cg_config import CGConfig, IlluminaConfig, RunInstruments
from cg.store.models import Analysis, Case
from cg.store.store import Store
from tests.store_helpers import StoreHelpers
from tests.typed_mock import TypedMock, create_typed_mock


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
    helpers.add_analysis(disk_store, case=case, upload_started=upload_started, uploading=True)

    # WHEN trying to upload an analysis that was started a long time ago
    result = cli_runner.invoke(upload, ["-f", case_id], obj=base_context)

    # THEN an exception should have be thrown
    assert result.exit_code != 0
    assert result.exception


def test_upload_force_restart(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    """Test that a case that is already uploading can be force restarted."""

    # GIVEN an analysis that is already uploading
    disk_store: Store = base_context.status_db
    case: Case = helpers.add_case(disk_store)
    case_id: str = case.internal_id

    helpers.add_analysis(disk_store, case=case, uploading=True)

    # WHEN trying to upload it again with the force restart flag
    result = cli_runner.invoke(upload, ["-f", case_id, "-r"], obj=base_context)

    # THEN it tries to restart the upload
    assert "already started" not in result.output


def test_upload_raw_data_case(cli_runner: CliRunner, mocker: MockerFixture):
    # GIVEN a raw data case with an analysis that has not been uploaded
    analysis: Analysis = create_autospec(Analysis, uploaded_at=None, upload_started_at=None)
    case: Case = create_autospec(
        Case,
        analyses=[analysis],
        data_analysis=Workflow.RAW_DATA,
        data_delivery=DataDelivery.SCOUT,
        internal_id="raw_data_case",
    )

    # GIVEN a status_db with the case
    status_db: Store = create_autospec(Store)
    status_db.verify_case_exists = Mock(return_value=True)
    status_db.get_case_by_internal_id = Mock(return_value=case)

    # GIVEN a RawDataUploadAPI can be instantiated
    raw_data_upload_api: TypedMock[RawDataUploadAPI] = create_typed_mock(RawDataUploadAPI)
    mocker.patch.object(base, "RawDataUploadAPI", return_value=raw_data_upload_api.as_type)

    # GIVEN a context with the status_db
    context: CGConfig = create_autospec(
        CGConfig,
        status_db=status_db,
        meta_apis={},
        delivery_path="delivery_path",
        run_instruments=create_autospec(
            RunInstruments,
            illumina=create_autospec(IlluminaConfig, demultiplexed_runs_dir="some_dir"),
        ),
    )

    # WHEN uploading the case
    result: Result = cli_runner.invoke(upload, ["--case", case.internal_id], obj=context)

    # THEN the upload succeeds and RawDataUploadAPI.upload is called
    assert result.exit_code == EXIT_SUCCESS
    raw_data_upload_api.as_mock.upload.assert_called_once_with(ctx=ANY, case=case, restart=False)
