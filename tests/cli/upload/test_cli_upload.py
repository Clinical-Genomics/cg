""" Test cg.cli.upload module """
from datetime import datetime, timedelta

from cg.cli.upload.base import upload
from cg.cli.upload.utils import LinkHelper
from cg.models.cg_config import CGConfig
from cg.store import Store, models
from click.testing import CliRunner
from tests.store_helpers import StoreHelpers


def test_all_samples_are_non_tumor(analysis_store: Store, case_id: str):
    """Test that all samples are non tumor"""

    case_obj = analysis_store.family(case_id)
    assert LinkHelper.all_samples_are_non_tumour(case_obj.links)


def test_all_samples_list_analyses(analysis_store: Store, case_id: str):
    """Test that all samples have an analysis type"""

    # GIVEN case obj where each sample is wgs analysis
    case_obj = analysis_store.family(case_id)

    # WHEN looking up the analysis type for the samples in the case
    analysis_types = LinkHelper.get_analysis_type_for_each_link(case_obj.links)

    # THEN all the samples should have analysis type 'wgs'
    assert len(set(analysis_types)) == 1 and analysis_types[0] == "wgs"


def test_upload_started_long_time_ago_raises_exception(
    cli_runner: CliRunner,
    base_context: CGConfig,
    helpers: StoreHelpers,
):
    """Test that an upload for a missing case does fail hard"""

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


def test_upload_force_restart(cli_runner: CliRunner, base_context: CGConfig, helpers: StoreHelpers):
    """Test that a case that is already uploading can be force restarted"""

    # GIVEN an analysis that is already uploading
    disk_store: Store = base_context.status_db
    case: models.Family = helpers.add_case(disk_store)
    case_id: str = case.internal_id

    helpers.add_analysis(disk_store, case=case, uploading=True)

    # WHEN trying to upload it again with the force restart flag
    result = cli_runner.invoke(upload, ["-f", case_id, "-r"], obj=base_context)

    # THEN it tries to restart the upload
    assert "already started" not in result.output
