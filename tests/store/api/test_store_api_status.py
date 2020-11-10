"""Tests the status part of the cg.store.api"""
from datetime import datetime, timedelta

from cg.constants import Pipeline


def test_samples_to_receive_external(sample_store, helpers):
    """Test fetching external sample"""
    store = sample_store
    # GIVEN a store with a mixture of samples
    assert store.samples().count() > 1

    # WHEN finding external samples to receive
    external_query = store.samples_to_receive(external=True)

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
    assert sample_store.samples_to_receive().count() == 1
    first_sample = sample_store.samples_to_receive().first()
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

    sample = helpers.add_sample(sample_store, loqus_id="uploaded_to_loqus")
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

    sample = helpers.add_sample(sample_store)
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

    sample = helpers.add_sample(sample_store)
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

    sample = helpers.add_sample(sample_store, loqus_id="uploaded_to_loqus")
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
    # GIVEN a store with an analysis without a completed_at date
    helpers.add_analysis(store=sample_store)

    # WHEN fetching all analyses that are ready for upload
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload()]

    # THEN no analysis object should be returned since they did not have a completed_at entry
    assert len(records) == 0


def test_analyses_to_upload_when_no_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload with no pipeline specified"""
    # GIVEN a store with one analysis
    helpers.add_analysis(store=sample_store, completed_at=timestamp)

    # WHEN fetching all analysis that are ready for upload without specifying pipeline
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=None)]

    # THEN one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_analysis_has_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing pipeline"""
    # GIVEN a store with an analysis that has been run with MIP
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=Pipeline.MIP_DNA)

    # WHEN fetching all analyses that are ready for upload and analysed with MIP
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=None)]

    # THEN one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_filtering_with_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing pipeline and using it in filtering"""
    # GIVEN a store with an analysis that is analysed with MIP
    pipeline = Pipeline.MIP_DNA
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=pipeline)

    # WHEN fetching all pipelines that are analysed with MIP
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=pipeline)]

    for analysis_obj in records:
        # THEN pipeline should be MIP in the analysis object
        assert analysis_obj.pipeline == str(pipeline)


def test_analyses_to_upload_with_pipeline_and_no_complete_at(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing pipeline and using it in filtering"""
    # GIVEN a store with an analysis that is analysed with MIP but does not have a completed_at
    pipeline = Pipeline.MIP_DNA
    helpers.add_analysis(store=sample_store, completed_at=None, pipeline=pipeline)

    # WHEN fetching all analyses that are ready for upload and analysed by MIP
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=pipeline)]

    # THEN no analysis object should be returned since they where not completed
    assert len(records) == 0


def test_analyses_to_upload_when_filtering_with_missing_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when missing pipeline and using it in filtering"""
    # GIVEN a store with an analysis that has been analysed with "missing_pipeline"
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=Pipeline.MIP_DNA)

    # WHEN fetching all analyses that was analysed with MIP
    records = [
        analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=Pipeline.FASTQ)
    ]

    # THEN no analysis object should be returned since there where no MIP analyses
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
