from datetime import datetime

import pytest

from cg.constants import SequencingRunDataAvailability
from cg.constants.constants import CaseActions, ControlOptions
from cg.constants.devices import RevioNames
from cg.constants.sequencing import Sequencers
from cg.services.run_devices.pacbio.data_transfer_service.dto import PacBioSequencingRunDTO
from cg.store.models import (
    Analysis,
    IlluminaSampleSequencingMetrics,
    IlluminaSequencingRun,
    PacbioSequencingRun,
    Sample,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_update_illumina_sequencing_run_availability(store_with_illumina_sequencing_data: Store):
    # GIVEN a store with Illumina Sequencing Runs that have data availability ON_DISK
    sequencing_run: IlluminaSequencingRun = (
        store_with_illumina_sequencing_data.get_illumina_sequencing_runs_by_data_availability(
            [SequencingRunDataAvailability.ON_DISK]
        )[0]
    )
    assert sequencing_run.data_availability == SequencingRunDataAvailability.ON_DISK

    # WHEN updating the data availability of a sequencing run
    store_with_illumina_sequencing_data.update_illumina_sequencing_run_data_availability(
        sequencing_run=sequencing_run, data_availability=SequencingRunDataAvailability.REQUESTED
    )

    # THEN the data availability of the sequencing run is updated
    assert sequencing_run.data_availability == SequencingRunDataAvailability.REQUESTED


def test_update_illumina_sequencing_run_has_backup(store_with_illumina_sequencing_data: Store):
    # GIVEN a store with Illumina Sequencing Runs that have backup status False
    sequencing_run: IlluminaSequencingRun = store_with_illumina_sequencing_data._get_query(
        IlluminaSequencingRun
    ).all()[0]
    assert sequencing_run.has_backup is False

    # WHEN updating the backup status of a sequencing run
    store_with_illumina_sequencing_data.update_illumina_sequencing_run_has_backup(
        sequencing_run=sequencing_run, has_backup=True
    )

    # THEN the backup status of the sequencing run is updated
    assert sequencing_run.has_backup is True


def test_update_sample_reads_illumina(
    store_with_illumina_sequencing_data: Store, selected_novaseq_x_sample_ids: list[str]
):
    # GIVEN a store with Illumina Sequencing Runs and a sample id
    sample: Sample = store_with_illumina_sequencing_data.get_sample_by_internal_id(
        selected_novaseq_x_sample_ids[0]
    )
    assert sample.reads == 0

    # WHEN updating the sample reads for a sequencing run
    store_with_illumina_sequencing_data.update_sample_reads_illumina(
        internal_id=selected_novaseq_x_sample_ids[0], sequencer_type=Sequencers.NOVASEQX
    )

    # THEN the total reads for the sample is updated
    total_reads_for_sample: int = 0
    sample_metrics: list[IlluminaSampleSequencingMetrics] = sample.sample_run_metrics
    for sample_metric in sample_metrics:
        total_reads_for_sample += sample_metric.total_reads_in_lane
    assert sample.reads == total_reads_for_sample


def test_update_sample_reads_illumina_fail_q30(
    store_with_illumina_sequencing_data: Store, selected_novaseq_x_sample_ids: list[str]
):
    # GIVEN a store with Illumina Sequencing Runs and a sample id
    sample: Sample = store_with_illumina_sequencing_data.get_sample_by_internal_id(
        selected_novaseq_x_sample_ids[0]
    )
    assert sample.reads == 0
    # GIVEN that the q30 for the lane is below the threshold for the sequencer type
    sample.sample_run_metrics[0].base_passing_q30_percent = 30

    # WHEN updating the sample reads for a sequencing run
    store_with_illumina_sequencing_data.update_sample_reads_illumina(
        internal_id=selected_novaseq_x_sample_ids[0], sequencer_type=Sequencers.NOVASEQX
    )

    # THEN the total reads for the sample is updated
    assert sample.reads == 0


def test_update_sample_reads_illumina_negative_control(
    store_with_illumina_sequencing_data: Store, selected_novaseq_x_sample_ids: list[str]
):
    # GIVEN a store with Illumina Sequencing Runs and a sample id
    sample: Sample = store_with_illumina_sequencing_data.get_sample_by_internal_id(
        selected_novaseq_x_sample_ids[0]
    )
    assert sample.reads == 0
    # GIVEN that the sample is a negative control sample
    sample.control = ControlOptions.NEGATIVE

    # WHEN updating the sample reads for a sequencing run
    store_with_illumina_sequencing_data.update_sample_reads_illumina(
        internal_id=selected_novaseq_x_sample_ids[0], sequencer_type=Sequencers.NOVASEQX
    )

    # THEN the total reads for the sample is updated
    total_reads_for_sample: int = 0
    sample_metrics: list[IlluminaSampleSequencingMetrics] = sample.sample_run_metrics
    for sample_metric in sample_metrics:
        total_reads_for_sample += sample_metric.total_reads_in_lane
    assert sample.reads == total_reads_for_sample


def test_update_sample_reads_pacbio_not_incremented(
    pacbio_barcoded_sample_internal_id: str,
    store: Store,
    helpers: StoreHelpers,
):
    """Tests that updating the reads for a PacBio sample does not increment the reads."""
    # GIVEN a store with a PacBio sample with reads
    sample: Sample = helpers.add_sample(store=store, internal_id=pacbio_barcoded_sample_internal_id)
    sample.reads = 1
    new_reads = 10000

    # WHEN updating the reads for the sample
    store.update_sample_reads_pacbio(
        internal_id=pacbio_barcoded_sample_internal_id, reads=new_reads
    )

    # THEN the reads for the sample are updated
    sample: Sample = store.get_sample_by_internal_id_strict(pacbio_barcoded_sample_internal_id)
    assert sample.reads == new_reads


@pytest.mark.parametrize(
    "sample_id_fixture",
    ["sample_id_sequenced_on_multiple_flow_cells", "pacbio_barcoded_sample_internal_id"],
    ids=["Illumina", "Pacbio"],
)
def test_update_sample_last_sequenced_at(
    store: Store,
    helpers: StoreHelpers,
    sample_id_fixture: str,
    timestamp_now: datetime,
    request: pytest.FixtureRequest,
):
    """Test updating the last sequenced at date for a sample."""
    # GIVEN a store with a sample
    sample_id: str = request.getfixturevalue(sample_id_fixture)
    sample: Sample = helpers.add_sample(store=store, internal_id=sample_id)
    assert sample.last_sequenced_at is None

    # WHEN updating the last sequenced at date for a sample
    store.update_sample_sequenced_at(internal_id=sample_id, date=timestamp_now)

    # THEN the last sequenced at date for the sample is updated
    sample: Sample = store.get_sample_by_internal_id(sample_id)
    assert sample.last_sequenced_at == timestamp_now


def test_update_analysis_uploaded_at(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store, timestamp_yesterday: datetime
):
    # GIVEN a store with an analysis
    analysis: Analysis = store_with_analyses_for_cases_not_uploaded_fluffy._get_query(
        Analysis
    ).first()
    assert analysis.uploaded_at != timestamp_yesterday

    # WHEN updating the uploaded_at field
    store_with_analyses_for_cases_not_uploaded_fluffy.update_analysis_uploaded_at(
        analysis_id=analysis.id, uploaded_at=timestamp_yesterday
    )

    # THEN the uploaded_at field is updated
    assert analysis.uploaded_at == timestamp_yesterday


def test_update_analysis_upload_started_at(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store, timestamp_yesterday: datetime
):
    # GIVEN a store with an analysis
    analysis: Analysis = store_with_analyses_for_cases_not_uploaded_fluffy._get_query(
        Analysis
    ).first()
    assert analysis.upload_started_at != timestamp_yesterday

    # WHEN updating the upload_started_at field
    store_with_analyses_for_cases_not_uploaded_fluffy.update_analysis_upload_started_at(
        analysis_id=analysis.id, upload_started_at=timestamp_yesterday
    )

    # THEN the upload_started_at field is updated
    assert analysis.upload_started_at == timestamp_yesterday


@pytest.mark.freeze_time
def test_update_analysis_completed_at(store: Store, helpers: StoreHelpers):
    """Test updating the completed at date for an analysis works properly."""
    # GIVEN a store with an analysis that has not been completed
    analysis: Analysis = helpers.add_analysis(store=store, completed_at=None)

    # WHEN updating the completed at date for an analysis
    store.update_analysis_completed_at(analysis_id=analysis.id, completed_at=datetime.now())

    # THEN the completed at date for the analysis is updated
    updated_analysis: Analysis = store.get_analysis_by_entry_id(analysis.id)
    assert updated_analysis.completed_at == datetime.now()


@pytest.mark.parametrize(
    "old_comment, expected_comment",
    [
        (None, "This is a new comment."),
        ("This is an old comment.", "This is an old comment.\nThis is a new comment."),
    ],
    ids=["no_existing_comment", "existing_comment"],
)
def test_update_analysis_comment(
    store: Store,
    helpers: StoreHelpers,
    old_comment: str | None,
    expected_comment: str,
):
    # GIVEN an analysis in store with a comment that may or may not exist
    analysis: Analysis = helpers.add_analysis(store=store)
    analysis.comment = old_comment

    # WHEN updating the comment for an analysis
    new_comment: str = "This is a new comment."
    store.update_analysis_comment(analysis_id=analysis.id, comment=new_comment)

    # THEN the comment for the analysis is updated
    assert analysis.comment == expected_comment


def test_update_analysis_housekeeper_version_id(store: Store, helpers: StoreHelpers):
    """Test updating the housekeeper version ID for an analysis works properly."""
    # GIVEN a store with an analysis that has no housekeeper version ID
    analysis: Analysis = helpers.add_analysis(store=store)
    assert analysis.housekeeper_version_id is None

    # WHEN updating the housekeeper version ID for an analysis
    new_version_id: int = 1234
    store.update_analysis_housekeeper_version_id(analysis_id=analysis.id, version_id=new_version_id)

    # THEN the housekeeper version ID for the analysis is updated
    updated_analysis: Analysis = store.get_analysis_by_entry_id(analysis.id)
    assert updated_analysis.housekeeper_version_id == new_version_id


@pytest.mark.freeze_time
def test_update_analysis_delivery_report_date(store: Store, helpers: StoreHelpers):
    """Test updating the delivery report created_at for an analysis works properly."""
    # GIVEN a store with an analysis without delivery report
    analysis: Analysis = helpers.add_analysis(store=store, delivery_reported_at=None)

    # WHEN updating the delivery report created_at for an analysis
    store.update_analysis_delivery_report_date(
        analysis_id=analysis.id, delivery_report_date=datetime.now()
    )

    # THEN the delivery report created_at for the analysis is updated
    updated_analysis: Analysis = store.get_analysis_by_entry_id(analysis.id)
    assert updated_analysis.delivery_report_created_at == datetime.now()


def test_update_case_action(analysis_store: Store, case_id: str):
    """Tests if actions of cases are changed to analyze."""
    # GIVEN a store with a case with action None
    action = analysis_store.get_case_by_internal_id_strict(internal_id=case_id).action

    assert action is None

    # WHEN setting the case to "analyze"
    analysis_store.update_case_action(case_internal_id=case_id, action=CaseActions.ANALYZE)
    new_action = analysis_store.get_case_by_internal_id_strict(internal_id=case_id).action

    # THEN the action should be set to analyze
    assert new_action == "analyze"


def test_update_pacbio_sequencing_run_comment(store: Store):
    # GIVEN a store with a PacBio sequencing run
    sequencing_run = store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, run_name="the_perfect_run"
        )
    )
    store.commit_to_store()

    # WHEN updating the comment of the sequencing run
    store.update_pacbio_sequencing_run_comment(
        id=sequencing_run.id, comment="The first comment of the new year! Happy 1926!"
    )

    # THEN the comment should have been updated
    updated_sequencing_run = (
        store._get_query(table=PacbioSequencingRun)
        .filter(PacbioSequencingRun.id == sequencing_run.id)
        .one()
    )
    assert updated_sequencing_run.comment == "The first comment of the new year! Happy 1926!"


def test_update_pacbio_sequencing_run_processed():
    pass
