"""Tests for store API status module."""

from sqlalchemy.orm import Query
from typing import List
from cg.constants import Pipeline, Priority
from cg.constants.subject import PhenotypeStatus
from cg.store import Store
from cg.store.models import Analysis, Application, Sample
from tests.store_helpers import StoreHelpers


def test_case_in_uploaded_observations(helpers: StoreHelpers, sample_store: Store, loqusdb_id: str):
    """Test retrieval of uploaded observations."""

    # GIVEN a case with observations that has been uploaded to Loqusdb
    analysis: Analysis = helpers.add_analysis(store=sample_store, pipeline=Pipeline.MIP_DNA)
    analysis.family.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(sample_store, loqusdb_id=loqusdb_id)
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
    analysis: Analysis = helpers.add_analysis(store=sample_store, pipeline=Pipeline.MIP_DNA)
    analysis.family.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(sample_store)
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
    analysis: Analysis = helpers.add_analysis(store=sample_store, pipeline=Pipeline.MIP_DNA)
    analysis.family.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(sample_store)
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
    analysis: Analysis = helpers.add_analysis(store=sample_store, pipeline=Pipeline.MIP_DNA)
    analysis.family.customer.loqus_upload = True
    sample: Sample = helpers.add_sample(sample_store, loqusdb_id=loqusdb_id)
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
    records: List[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload()
    ]

    # THEN no analysis object should be returned since they did not have a completed_at entry
    assert len(records) == 0


def test_analyses_to_upload_when_no_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload with no pipeline specified."""
    # GIVEN a store with one analysis
    helpers.add_analysis(store=sample_store, completed_at=timestamp)

    # WHEN fetching all analysis that are ready for upload without specifying pipeline
    records: List[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload(pipeline=None)
    ]

    # THEN one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_analysis_has_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing pipeline."""
    # GIVEN a store with an analysis that has been run with MIP
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=Pipeline.MIP_DNA)

    # WHEN fetching all analyses that are ready for upload and analysed with MIP
    records: List[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload(pipeline=None)
    ]

    # THEN one analysis object should be returned
    assert len(records) == 1


def test_analyses_to_upload_when_filtering_with_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing pipeline and using it in filtering."""
    # GIVEN a store with an analysis that is analysed with MIP
    pipeline = Pipeline.MIP_DNA
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=pipeline)

    # WHEN fetching all pipelines that are analysed with MIP
    records: List[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload(pipeline=pipeline)
    ]

    for analysis_obj in records:
        # THEN pipeline should be MIP in the analysis object
        assert analysis_obj.pipeline == str(pipeline)


def test_analyses_to_upload_with_pipeline_and_no_complete_at(helpers, sample_store, timestamp):
    """Test analyses to upload to when existing pipeline and using it in filtering."""
    # GIVEN a store with an analysis that is analysed with MIP but does not have a completed_at
    pipeline = Pipeline.MIP_DNA
    helpers.add_analysis(store=sample_store, completed_at=None, pipeline=pipeline)

    # WHEN fetching all analyses that are ready for upload and analysed by MIP
    records: List[Analysis] = [
        analysis_obj for analysis_obj in sample_store.get_analyses_to_upload(pipeline=pipeline)
    ]

    # THEN no analysis object should be returned since they where not completed
    assert len(records) == 0


def test_analyses_to_upload_when_filtering_with_missing_pipeline(helpers, sample_store, timestamp):
    """Test analyses to upload to when missing pipeline and using it in filtering."""
    # GIVEN a store with an analysis that has been analysed with "missing_pipeline"
    helpers.add_analysis(store=sample_store, completed_at=timestamp, pipeline=Pipeline.MIP_DNA)

    # WHEN fetching all analyses that was analysed with MIP
    records: List[Analysis] = [
        analysis_obj
        for analysis_obj in sample_store.get_analyses_to_upload(pipeline=Pipeline.FASTQ)
    ]

    # THEN no analysis object should be returned since there where no MIP analyses
    assert len(records) == 0


def test_set_case_action(analysis_store: Store, case_id):
    """Tests if actions of cases are changed to analyze."""
    # Given a store with a case with action None
    action = analysis_store.get_case_by_internal_id(internal_id=case_id).action

    assert action == None

    # When setting the case to "analyze"
    analysis_store.set_case_action(case_internal_id=case_id, action="analyze")
    new_action = analysis_store.get_case_by_internal_id(internal_id=case_id).action

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
