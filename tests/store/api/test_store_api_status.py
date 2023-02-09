"""Tests for store API status module."""

from alchy import Query

from cg.constants import Pipeline, Priority
from cg.constants.subject import PhenotypeStatus
from cg.store import Store, models
from cg.store.models import Application, Family, Sample
from tests.store_helpers import StoreHelpers


def test_samples_to_receive_external(sample_store, helpers):
    """Test fetching external sample."""
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


def test_case_in_uploaded_observations(helpers: StoreHelpers, sample_store: Store, loqusdb_id: str):
    """Test retrieval of uploaded observations."""

    # GIVEN a case with observations that has been uploaded to Loqusdb
    analysis: models.Analysis = helpers.add_analysis(store=sample_store, pipeline=Pipeline.MIP_DNA)
    analysis.family.customer.loqus_upload = True
    sample: models.Sample = helpers.add_sample(sample_store, loqusdb_id=loqusdb_id)
    sample_store.relate_sample(analysis.family, sample, PhenotypeStatus.UNKNOWN)
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is not None

    # WHEN getting observations to upload
    uploaded_observations: Query = sample_store.observations_uploaded()

    # THEN the case should be in the returned query
    assert analysis.family in uploaded_observations


def test_case_not_in_uploaded_observations(helpers: StoreHelpers, sample_store: Store):
    """Test retrieval of uploaded observations that have not been uploaded to Loqusdb."""

    # GIVEN a case with observations that has not been uploaded to loqusdb
    analysis: models.Analysis = helpers.add_analysis(store=sample_store, pipeline=Pipeline.MIP_DNA)
    analysis.family.customer.loqus_upload = True
    sample: models.Sample = helpers.add_sample(sample_store)
    sample_store.relate_sample(analysis.family, sample, PhenotypeStatus.UNKNOWN)
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is None

    # WHEN getting observations to upload
    uploaded_observations: Query = sample_store.observations_uploaded()

    # THEN the case should not be in the returned query
    assert analysis.family not in uploaded_observations


def test_case_in_observations_to_upload(helpers: StoreHelpers, sample_store: Store):
    """Test extraction of ready to be uploaded to Loqusdb cases."""

    # GIVEN a case with completed analysis and samples w/o loqusdb_id
    analysis: models.Analysis = helpers.add_analysis(store=sample_store, pipeline=Pipeline.MIP_DNA)
    analysis.family.customer.loqus_upload = True
    sample: models.Sample = helpers.add_sample(sample_store)
    sample_store.relate_sample(analysis.family, sample, PhenotypeStatus.UNKNOWN)
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is None

    # WHEN getting observations to upload
    observations_to_upload: Query = sample_store.observations_to_upload()

    # THEN the case should be in the returned query
    assert analysis.family in observations_to_upload


def test_case_not_in_observations_to_upload(
    helpers: StoreHelpers, sample_store: Store, loqusdb_id: str
):
    """Test case extraction that should not be uploaded to Loqusdb."""

    # GIVEN a case with completed analysis and samples with a Loqusdb ID
    analysis: models.Analysis = helpers.add_analysis(store=sample_store, pipeline=Pipeline.MIP_DNA)
    analysis.family.customer.loqus_upload = True
    sample: models.Sample = helpers.add_sample(sample_store, loqusdb_id=loqusdb_id)
    sample_store.relate_sample(analysis.family, sample, PhenotypeStatus.UNKNOWN)
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is not None

    # WHEN getting observations to upload
    observations_to_upload: Query = sample_store.observations_to_upload()

    # THEN the case should not be in the returned query
    assert analysis.family not in observations_to_upload


def test_analyses_to_upload_when_not_completed_at(helpers, sample_store):
    """Test analyses to upload with no completed_at date."""
    # GIVEN a store with an analysis without a completed_at date
    helpers.add_analysis(store=sample_store)

    # WHEN fetching all analyses that are ready for upload
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload()]

    # THEN no analysis object should be returned since they did not have a completed_at entry
    assert len(records) == 0


def test_analyses_to_upload_when_no_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload with no pipeline specified."""
    # GIVEN a store with one analysis
    helpers.add_analysis(store=sample_store, completed_at=timestamp)

    # WHEN fetching all analysis that are ready for upload without specifying pipeline
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=None)]

    # THEN one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_analysis_has_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing pipeline."""
    # GIVEN a store with an analysis that has been run with MIP
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=Pipeline.MIP_DNA)

    # WHEN fetching all analyses that are ready for upload and analysed with MIP
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=None)]

    # THEN one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_filtering_with_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing pipeline and using it in filtering."""
    # GIVEN a store with an analysis that is analysed with MIP
    pipeline = Pipeline.MIP_DNA
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=pipeline)

    # WHEN fetching all pipelines that are analysed with MIP
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=pipeline)]

    for analysis_obj in records:
        # THEN pipeline should be MIP in the analysis object
        assert analysis_obj.pipeline == str(pipeline)


def test_analyses_to_upload_with_pipeline_and_no_complete_at(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing pipeline and using it in filtering."""
    # GIVEN a store with an analysis that is analysed with MIP but does not have a completed_at
    pipeline = Pipeline.MIP_DNA
    helpers.add_analysis(store=sample_store, completed_at=None, pipeline=pipeline)

    # WHEN fetching all analyses that are ready for upload and analysed by MIP
    records = [analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=pipeline)]

    # THEN no analysis object should be returned since they where not completed
    assert len(records) == 0


def test_analyses_to_upload_when_filtering_with_missing_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when missing pipeline and using it in filtering."""
    # GIVEN a store with an analysis that has been analysed with "missing_pipeline"
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=Pipeline.MIP_DNA)

    # WHEN fetching all analyses that was analysed with MIP
    records = [
        analysis_obj for analysis_obj in sample_store.analyses_to_upload(pipeline=Pipeline.FASTQ)
    ]

    # THEN no analysis object should be returned since there where no MIP analyses
    assert len(records) == 0


def test_multiple_analyses(analysis_store, helpers, timestamp_now, timestamp_yesterday):
    """Tests that analyses that are not latest are not returned."""

    # GIVEN an analysis that is not delivery reported but there exists a newer analysis
    case = helpers.add_case(analysis_store)
    analysis_oldest = helpers.add_analysis(
        analysis_store,
        case=case,
        started_at=timestamp_yesterday,
        uploaded_at=timestamp_yesterday,
        delivery_reported_at=None,
    )
    analysis_store.add_commit(analysis_oldest)
    analysis_newest = helpers.add_analysis(
        analysis_store,
        case=case,
        started_at=timestamp_now,
        uploaded_at=timestamp_now,
        delivery_reported_at=None,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
    analysis_store.relate_sample(
        family=analysis_oldest.family, sample=sample, status=PhenotypeStatus.UNKNOWN
    )

    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.latest_analyses().all()

    # THEN only the newest analysis should be returned
    assert analysis_newest in analyses
    assert analysis_oldest not in analyses


def test_set_case_action(analysis_store, case_id):
    """Tests if actions of cases are changed to analyze."""
    # Given a store with a case with action None
    action = analysis_store.Family.query.filter(Family.internal_id == case_id).first().action

    assert action == None

    # When setting the case to "analyze"
    analysis_store.set_case_action(case_id=case_id, action="analyze")
    new_action = analysis_store.Family.query.filter(Family.internal_id == case_id).first().action

    # Then the action should be set to analyze
    assert new_action == "analyze"


def test_sequencing_qc_priority_express_sample_with_one_half_of_the_reads(
    base_store: Store, helpers, timestamp_now
):
    """Test if priority express sample(s), having more than 50% of the application target reads, pass sample QC."""

    # GIVEN a database with a case which has an express sample with half the amount of reads
    sample: Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)
    application: Application = sample.application_version.application
    application.target_reads = 40
    sample.reads = 20
    sample.priority = Priority.express

    # WHEN retrieving the sequencing qc property of a the express sample
    sequencing_qc_ok: bool = sample.sequencing_qc

    # THEN the qc property should be True
    assert sequencing_qc_ok


def test_sequencing_qc_priority_standard_sample_with_one_half_of_the_reads(
    base_store: Store, helpers, timestamp_now
):
    """Test if priority standard sample(s), having more than 50% of the application target reads, pass sample QC."""

    # GIVEN a database with a case which has an normal sample with half the amount of reads
    sample: Sample = helpers.add_sample(base_store, sequenced_at=timestamp_now)
    application: Application = sample.application_version.application
    application.target_reads = 40
    sample.reads = 20
    sample.priority = Priority.standard

    # WHEN retrieving the sequencing qc property of a the normal sample
    sequencing_qc_ok: bool = sample.sequencing_qc

    # THEN the qc property should be False
    assert not sequencing_qc_ok
