from datetime import datetime

import pytest

from cg.constants import SequencingRunDataAvailability
from cg.constants.constants import ControlOptions
from cg.constants.sequencing import Sequencers
from cg.store.models import Analysis, IlluminaSampleSequencingMetrics, IlluminaSequencingRun, Sample
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


def test_update_sample_reads_pacbio(
    pacbio_barcoded_sample_internal_id: str,
    store: Store,
    helpers: StoreHelpers,
):
    """Test updating the reads for a PacBio sample."""
    # GIVEN a store with a PacBio sample
    sample: Sample = helpers.add_sample(store=store, internal_id=pacbio_barcoded_sample_internal_id)
    assert sample
    assert sample.reads == 0
    reads: int = 10000

    # WHEN updating the reads for the sample
    store.update_sample_reads(internal_id=pacbio_barcoded_sample_internal_id, reads=reads)

    # THEN the reads for the sample is updated
    sample: Sample = store.get_sample_by_internal_id(pacbio_barcoded_sample_internal_id)
    assert sample.reads == reads


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
