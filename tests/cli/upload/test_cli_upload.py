""" Test cg.cli.upload module """
from datetime import datetime, timedelta

from cg.cli.upload.utils import LinkHelper
from cg.store import Store


def test_all_samples_are_non_tumor(analysis_store, case_id):
    """Test that all samples are non tumor"""

    case_obj = analysis_store.family(case_id)
    assert LinkHelper.all_samples_are_non_tumour(case_obj.links)


def test_all_samples_list_analyses(analysis_store, case_id):
    """Test that all samples have an analysis type"""

    # GIVEN case obj where each sample is wgs analysis
    case_obj = analysis_store.family(case_id)

    # WHEN looking up the analysis type for the samples in the case
    analysis_types = LinkHelper.get_analysis_type_for_each_link(case_obj.links)

    # THEN all the samples should have analysis type 'wgs'
    assert len(set(analysis_types)) == 1 and analysis_types[0] == "wgs"


def test_upload_fails_hard_on_faulty_family(invoke_cli, disk_store: Store):
    """Test that an upload for a missing case does fail hard """

    # GIVEN empty database
    case_id = "dummy_case"

    # WHEN trying to upload with a case that doesn't exist
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", case_id])

    # THEN it fails hard and reports that it is missing the case
    assert result.exit_code != 0
    assert case_id in result.output
    assert "family not found" in result.output


def test_upload_fails_hard_on_faulty_analysis(invoke_cli, disk_store: Store, helpers):
    """Test that an upload for a missing analysis does fail hard """

    # GIVEN empty database
    case_id = helpers.add_case(disk_store).internal_id

    # WHEN trying to upload with a analysis that doesn't exist
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", case_id])

    # THEN it fails hard and reports that it is missing the analysis
    assert result.exit_code != 0
    assert case_id in result.output
    assert "no analysis exists" in result.output


def test_upload_doesnt_invoke_dually_for_same_case(invoke_cli, disk_store: Store, helpers):
    """Test that a case that is already uploading can't be uploaded at the same time"""

    # GIVEN an analysis that is already uploading
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    helpers.add_analysis(disk_store, case=case, uploading=True)

    # WHEN trying to upload it again
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", case_id])

    # THEN it gracefully skips and reports that it is already uploading
    assert result.exit_code == 0
    assert not result.exception
    assert "already started" in result.output


def test_upload_started_long_time_ago_raises_exception(invoke_cli, disk_store: Store, helpers):
    """Test that an upload for a missing case does fail hard """

    # GIVEN an analysis that is already uploading since a week ago
    case = helpers.add_case(disk_store)
    case_id = case.internal_id
    today = datetime.now()
    upload_started = today - timedelta(hours=100)
    helpers.add_analysis(disk_store, case=case, uploading=True, upload_started=upload_started)

    # WHEN trying to upload an analysis that was started a long time ago
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", case_id])

    # THEN an exception should have be thrown
    assert result.exit_code != 0
    assert result.exception


def test_upload_force_restart(invoke_cli, disk_store: Store, helpers):
    """Test that a case that is already uploading can be force restarted"""

    # GIVEN an analysis that is already uploading
    case = helpers.add_case(disk_store)
    case_id = case.internal_id

    helpers.add_analysis(disk_store, case=case, uploading=True)

    # WHEN trying to upload it again with the force restart flag
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", case_id, "-r"])

    # THEN it tries to restart the upload
    assert "already started" not in result.output


def test_upload_uploaded_fails_hard(invoke_cli, disk_store: Store, helpers):
    """Test that a case that has already been uploaded can't be uploaded"""

    # GIVEN an analysis that has been uploaded
    case = helpers.add_case(disk_store)
    case_id = case.internal_id

    helpers.add_analysis(disk_store, case=case, uploaded_at=datetime.now())

    # WHEN trying to upload it again
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", case_id])

    # THEN it fails hard and reports that it is already uploaded
    assert result.exit_code != 0
    assert "already uploaded" in result.output
