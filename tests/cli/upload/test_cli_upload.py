""" Test cg.cli.upload module """
from datetime import datetime, timedelta

from cg.cli.upload.utils import LinkHelper
from cg.store import Store


def test_all_samples_are_non_tumor(analysis_store):
    """Test that all samples are non tumor"""

    family_obj = analysis_store.family("yellowhog")
    assert LinkHelper.all_samples_are_non_tumour(family_obj.links)


def test_all_samples_data_analysis(analysis_store):
    """Test that all samples have data analysis"""

    family_obj = analysis_store.family("yellowhog")
    assert LinkHelper.all_samples_data_analysis(family_obj.links, ["mip"])


def test_all_samples_list_analyses(analysis_store):
    """Test that all samples have an analysis type"""

    # GIVEN family obj where each sample is wgs analysis
    family_obj = analysis_store.family("yellowhog")

    # WHEN looking up the analysis type for the samples in the family
    analysis_types = LinkHelper.all_samples_list_analyses(family_obj.links)

    # THEN all the samples should have analysis type 'wgs'
    assert len(set(analysis_types)) == 1 and analysis_types[0] == "wgs"


def test_upload_fails_hard_on_faulty_family(invoke_cli, disk_store: Store):
    """Test that an upload for a missing family does fail hard """

    # GIVEN empty database
    family_id = "dummy_family"

    # WHEN trying to upload with a family that doesn't exist
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", family_id])

    # THEN it fails hard and reports that it is missing the family
    assert result.exit_code != 0
    assert family_id in result.output
    assert "family not found" in result.output


def test_upload_fails_hard_on_faulty_analysis(invoke_cli, disk_store: Store):
    """Test that an upload for a missing analysis does fail hard """

    # GIVEN empty database
    family_id = add_family(disk_store).internal_id

    # WHEN trying to upload with a analysis that doesn't exist
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", family_id])

    # THEN it fails hard and reports that it is missing the analysis
    assert result.exit_code != 0
    assert family_id in result.output
    assert "no analysis exists" in result.output


def test_upload_doesnt_invoke_dually_for_same_case(invoke_cli, disk_store: Store):
    """Test that a case that is already uploading can't be uploaded at the same time"""

    # GIVEN an analysis that is already uploading
    family_id = add_family(disk_store).internal_id
    add_analysis(disk_store, family_id=family_id, uploading=True)

    # WHEN trying to upload it again
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", family_id])

    # THEN it gracefully skips and reports that it is already uploading
    assert result.exit_code == 0
    assert not result.exception
    assert "already started" in result.output


def test_upload_started_long_time_ago_raises_exception(invoke_cli, disk_store: Store):
    """Test that an upload for a missing family does fail hard """

    # GIVEN an analysis that is already uploading since a week ago
    family_id = add_family(disk_store).internal_id
    today = datetime.now()
    upload_started = today - timedelta(hours=100)
    add_analysis(
        disk_store, family_id=family_id, uploading=True, upload_started=upload_started
    )

    # WHEN trying to upload an analysis that was started a long time ago
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", family_id])

    # THEN an exception should have be thrown
    assert result.exit_code != 0
    assert result.exception


def test_upload_force_restart(invoke_cli, disk_store: Store):
    """Test that a case that is already uploading can be force restarted"""

    # GIVEN an analysis that is already uploading
    family_id = add_family(disk_store).internal_id
    add_analysis(disk_store, family_id=family_id, uploading=True)

    # WHEN trying to upload it again with the force restart flag
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", family_id, "-r"])

    # THEN it tries to restart the upload
    assert "already started" not in result.output


def test_upload_uploaded_fails_hard(invoke_cli, disk_store: Store):
    """Test that a case that has already been uploaded can't be uploaded"""

    # GIVEN an analysis that has been uploaded
    family_id = add_family(disk_store).internal_id
    add_analysis(disk_store, family_id=family_id, uploaded=True)

    # WHEN trying to upload it again
    result = invoke_cli(["--database", disk_store.uri, "upload", "-f", family_id])

    # THEN it fails hard and reports that it is already uploaded
    assert result.exit_code != 0
    assert "already uploaded" in result.output


def add_panel(disk_store, panel_id="panel_test", customer_id="cust_test"):
    """utility function to set a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.add_panel(
        customer=customer,
        name=panel_id,
        abbrev=panel_id,
        version=1.0,
        date=datetime.now(),
        genes=1,
    )
    disk_store.add_commit(panel)
    return panel


def add_application(disk_store, application_tag="dummy_tag"):
    """utility function to set an application to use in tests"""
    application = disk_store.add_application(
        tag=application_tag,
        category="wgs",
        description="dummy_description",
        percent_kth=80,
    )
    disk_store.add_commit(application)
    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.add_version(
        application, 1, valid_from=datetime.now(), prices=prices
    )

    disk_store.add_commit(version)
    return application


def ensure_application_version(disk_store, application_tag="dummy_tag"):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(
            tag=application_tag,
            category="wgs",
            description="dummy_description",
            percent_kth=80,
        )
        disk_store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(
            application, 1, valid_from=datetime.now(), prices=prices
        )

        disk_store.add_commit(version)
    return version


def ensure_customer(disk_store, customer_id="cust_test"):
    """utility function to return existing or create customer for tests"""
    customer_group = disk_store.customer_group("dummy_group")
    if not customer_group:
        customer_group = disk_store.add_customer_group("dummy_group", "dummy group")

        customer = disk_store.add_customer(
            internal_id=customer_id,
            name="Test Customer",
            scout_access=False,
            customer_group=customer_group,
            invoice_address="dummy_address",
            invoice_reference="dummy_reference",
        )
        disk_store.add_commit(customer)
    customer = disk_store.customer(customer_id)
    return customer


def add_family(disk_store, family_name="family_test", customer_id="cust_test"):
    """utility function to set a family to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel_id = add_panel(disk_store).name
    family = disk_store.add_family(name=family_name, panels=panel_id)
    family.customer = customer
    disk_store.add_commit(family)
    return family


def add_analysis(
    disk_store,
    family_id,
    uploading=False,
    uploaded=False,
    upload_started=datetime.now(),
):
    """utility function to add an analysis to use in tests"""
    family = disk_store.family(family_id)
    analysis = disk_store.add_analysis(pipeline="pipeline_test")
    analysis.family = family
    if uploading:
        analysis.upload_started_at = upload_started
    if uploaded:
        analysis.uploaded_at = datetime.now()
    disk_store.add_commit(analysis)
    return analysis
