"""Tests the status part of the cg.store.api"""
from datetime import datetime, timedelta


def test_samples_to_receive_external(sample_store, helpers):
    """Test fetching external sample"""
    store = sample_store
    # GIVEN a store with a mixture of samples
    assert store.samples().count() > 1

    # WHEN finding external samples to receive
    external_query = store.samples_to_recieve(external=True)

    # THEN assert that only the external sample is returned
    assert external_query.count() == 1

    first_sample = external_query.first()
    # THEN assert that the sample is external in database
    assert first_sample.application_version.application.is_external is True
    # THEN assert that the sample is does not have a received at stamp
    assert first_sample.received_at is None


def test_samples_to_receive_internal(sample_store):
    # GIVEN a store with samples in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.received_at]) > 1

    # WHEN finding which samples are in queue to receive
    assert sample_store.samples_to_recieve().count() == 1
    first_sample = sample_store.samples_to_recieve().first()
    assert first_sample.application_version.application.is_external is False
    assert first_sample.received_at is None


def test_samples_to_sequence(sample_store):
    # GIVEN a store with sample in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.sequenced_at]) >= 1

    # WHEN finding which samples are in queue to be sequenced
    sequence_samples = sample_store.samples_to_sequence()

    # THEN it should list the received and partly sequenced samples
    assert sequence_samples.count() == 2
    assert {sample.name for sample in sequence_samples} == set(
        ["sequenced-partly", "received-prepared"]
    )
    for sample in sequence_samples:
        assert sample.sequenced_at is None
        if sample.name == "sequenced-partly":
            assert sample.reads > 0


def test_case_in_uploaded_observations(helpers, sample_store):
    # GIVEN a case with observations that has been uploaded to loqusdb
    analysis = helpers.add_analysis(store=sample_store)

    sample = add_sample(sample_store, uploaded_to_loqus=True)
    sample_store.relate_sample(analysis.family, sample, "unknown")
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is not None

    # WHEN getting observations to upload
    uploaded_observations = sample_store.observations_uploaded()

    # THEN the case should be in the returned collection
    assert analysis.family in uploaded_observations


def test_case_not_in_uploaded_observations(helpers, sample_store):
    # GIVEN a case with observations that has not been uploaded to loqusdb
    analysis = helpers.add_analysis(store=sample_store)

    sample = add_sample(sample_store)
    sample_store.relate_sample(analysis.family, sample, "unknown")
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is None

    # WHEN getting observations to upload
    uploaded_observations = sample_store.observations_uploaded()

    # THEN the case should not be in the returned collection
    assert analysis.family not in uploaded_observations


def test_case_in_observations_to_upload(helpers, sample_store):
    # GIVEN a case with completed analysis and samples w/o loqus_id
    analysis = helpers.add_analysis(store=sample_store)

    sample = add_sample(sample_store)
    sample_store.relate_sample(analysis.family, sample, "unknown")
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is None

    # WHEN getting observations to upload
    observations_to_upload = sample_store.observations_to_upload()

    # THEN the case should be in the returned collection
    assert analysis.family in observations_to_upload


def test_case_not_in_observations_to_upload(helpers, sample_store):
    # GIVEN a case with completed analysis and samples w loqus_id
    analysis = helpers.add_analysis(store=sample_store)

    sample = add_sample(sample_store, uploaded_to_loqus=True)
    sample_store.relate_sample(analysis.family, sample, "unknown")
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is not None

    # WHEN getting observations to upload
    observations_to_upload = sample_store.observations_to_upload()

    # THEN the case should not be in the returned collection
    assert analysis.family not in observations_to_upload


def test_analyses_to_upload_when_not_completed_at(helpers, sample_store):
    """Test analyses to upload with no completed_at date"""
    # GIVEN a case with completed analysis
    helpers.add_analysis(store=sample_store)

    # WHEN no analyses are completed
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload()]

    # THEN no analysis object should be returned
    assert len(records) == 0


def test_analyses_to_upload_when_no_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload with no pipeline specified"""
    # GIVEN a case with completed analysis
    helpers.add_analysis(store=sample_store, completed_at=timestamp)

    # WHEN uploading without a pipeline specified
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=None)]

    # THEN one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_existing_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when exisiting pipeline"""
    # GIVEN a case with completed analysis
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline="MIP")

    # WHEN uploading without a pipeline specified
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=None)]

    # THEN at least one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_filtering_with_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when exisiting pipeline and using it in filtering"""
    # GIVEN a case with completed analysis
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline="MIP")

    # WHEN uploading without a pipeline specified
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline="MIP")]

    # THEN at least one analysis object should be returned
    assert len(records) == 1

    for analysis_obj in records:
        # THEN pipeline should be MIP in the analysis object
        assert analysis_obj.pipeline == "MIP"


def test_analyses_to_upload_when_filtering_with_missing_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when missing pipeline and using it in filtering"""
    # GIVEN a case with completed analysis
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline="missing_pipeline")

    # WHEN uploading without a pipeline specified
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline="MIP")]

    # THEN no analysis object should be returned
    assert len(records) == 0


def test_multiple_analyses(analysis_store, helpers):
    """Tests that analyses that are not latest are not returned"""

    # GIVEN an analysis that is not delivery reported but there exists a newer analysis
    timestamp = datetime.now()
    family = helpers.add_family(analysis_store)
    analysis_oldest = helpers.add_analysis(
        analysis_store,
        family=family,
        started_at=timestamp - timedelta(days=1),
        uploaded_at=timestamp - timedelta(days=1),
        delivery_reported_at=None,
    )
    analysis_store.add_commit(analysis_oldest)
    analysis_newest = helpers.add_analysis(
        analysis_store,
        family=family,
        started_at=timestamp,
        uploaded_at=timestamp,
        delivery_reported_at=None,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis_oldest.family, sample=sample, status="unknown")

    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.latest_analyses().all()

    # THEN only the newest analysis should be returned
    assert analysis_newest in analyses
    assert analysis_oldest not in analyses


def ensure_customer(store, customer_id="cust_test"):
    """utility function to return existing or create customer for tests"""
    customer_group = store.customer_group("dummy_group")
    if not customer_group:
        customer_group = store.add_customer_group("dummy_group", "dummy group")

        customer = store.add_customer(
            internal_id=customer_id,
            name="Test Customer",
            scout_access=False,
            customer_group=customer_group,
            invoice_address="dummy_address",
            invoice_reference="dummy_reference",
        )
        store.add_commit(customer)
    customer = store.customer(customer_id)
    return customer


def ensure_panel(store, panel_id="panel_test", customer_id="cust_test"):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(store, customer_id)
    panel = store.panel(panel_id)
    if not panel:
        panel = store.add_panel(
            customer=customer,
            name=panel_id,
            abbrev=panel_id,
            version=1.0,
            date=datetime.now(),
            genes=1,
        )
        store.add_commit(panel)
    return panel


def ensure_application_version(disk_store, application_tag="dummy_tag"):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(
            tag=application_tag, category="wgs", description="dummy_description", percent_kth=80
        )
        disk_store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(), prices=prices)

        disk_store.add_commit(version)
    return version


def add_sample(store, sample_name="sample_test", uploaded_to_loqus=None):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_name, sex="unknown")
    sample.application_version_id = application_version_id
    sample.customer = customer
    if uploaded_to_loqus:
        sample.loqusdb_id = uploaded_to_loqus
    store.add_commit(sample)
    return sample
