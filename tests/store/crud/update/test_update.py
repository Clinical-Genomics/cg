from datetime import datetime

from cg.constants import SequencingRunDataAvailability
from cg.store.models import IlluminaSequencingRun, Sample
from cg.store.store import Store


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
        internal_id=selected_novaseq_x_sample_ids[0]
    )

    # THEN the total reads for the sample is updated
    total_reads_for_sample: int = 0
    sample_metrics: list[IlluminaSampleSequencingMetrics] = sample.sample_run_metrics
    for sample_metric in sample_metrics:
        total_reads_for_sample += sample_metric.total_reads_in_lane
    assert sample.reads == total_reads_for_sample


def test_update_sample_last_sequenced_at(
    store_with_illumina_sequencing_data: Store,
    selected_novaseq_x_sample_ids: list[str],
    timestamp_now: datetime,
):
    # GIVEN a store with Illumina Sequencing Runs and a sample id
    sample: Sample = store_with_illumina_sequencing_data.get_sample_by_internal_id(
        selected_novaseq_x_sample_ids[0]
    )
    assert sample.last_sequenced_at is None

    # WHEN updating the last sequenced at date for a sample
    store_with_illumina_sequencing_data.update_sample_sequenced_at(
        internal_id=selected_novaseq_x_sample_ids[0], date=timestamp_now
    )

    # THEN the last sequenced at date for the sample is updated
    assert sample.last_sequenced_at == timestamp_now
