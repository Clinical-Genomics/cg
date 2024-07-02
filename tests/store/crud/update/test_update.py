from cg.constants import SequencingRunDataAvailability
from cg.store.models import IlluminaSequencingRun
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
