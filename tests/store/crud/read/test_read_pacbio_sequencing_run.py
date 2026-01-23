import pytest

from cg.constants.devices import RevioNames
from cg.exc import PacbioSequencingRunNotFoundError
from cg.services.run_devices.pacbio.data_transfer_service.dto import PacBioSequencingRunDTO
from cg.store.models import PacbioSequencingRun
from cg.store.store import Store


def test_get_pacbio_sequencing_runs(
    store: Store,
):
    # GIVEN a store with two runs
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, internal_id="older"
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.WILMA, internal_id="newer"
        )
    )

    # WHEN fetching the runs
    runs, total_count = store.get_pacbio_sequencing_runs()

    # THEN the two runs should be returned
    assert runs[0].internal_id == "newer"
    assert runs[1].internal_id == "older"
    assert total_count == 2


def test_get_pacbio_sequencing_runs_with_pagination(
    store: Store,
):
    # GIVEN a store with two runs
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, internal_id="pinocchio"
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.WILMA, internal_id="grinch"
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, internal_id="sauron"
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.WILMA, internal_id="jesus_christ"
        )
    )

    # WHEN fetching the runs
    runs, total_count = store.get_pacbio_sequencing_runs(page=2, page_size=2)

    # THEN the two runs should be returned
    assert runs[0].internal_id == "grinch"
    assert runs[1].internal_id == "pinocchio"
    assert total_count == 4


def test_get_pacbio_sequencing_run_by_id_successful(store: Store):
    # GIVEN a store with a Pacbio sequencing run
    sequencing_run: PacbioSequencingRun = store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, internal_id="pinocchio"
        )
    )
    store.commit_to_store()

    # WHEN getting the sequencing run by id
    fetched_run: PacbioSequencingRun = store.get_pacbio_sequencing_run_by_id(sequencing_run.id)

    # THEN the fetched run is as expected
    assert fetched_run == sequencing_run


def test_get_pacbio_sequencing_run_by_id_unsuccessful(store: Store):
    # GIVEN a store with a Pacbio sequencing run
    sequencing_run: PacbioSequencingRun = store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, internal_id="pinocchio"
        )
    )
    store.commit_to_store()

    # WHEN getting the sequencing run by the wrong id
    # THEN an error stating that the run was not found is raised
    with pytest.raises(PacbioSequencingRunNotFoundError):
        store.get_pacbio_sequencing_run_by_id(sequencing_run.id + 1)


def test_get_pacbio_sequencing_run_by_run_name_successful(store: Store):
    # GIVEN a store with a Pacbio sequencing run
    sequencing_run: PacbioSequencingRun = store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, internal_id="pinocchio"
        )
    )
    store.commit_to_store()

    # WHEN getting the sequencing run by internal_id
    fetched_run: PacbioSequencingRun = store.get_pacbio_sequencing_run_by_internal_id(
        sequencing_run.internal_id
    )

    # THEN the fetched run is as expected
    assert fetched_run == sequencing_run


def test_get_pacbio_sequencing_run_by_run_name_unsuccessful(store: Store):
    # GIVEN a store with a Pacbio sequencing run
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, internal_id="pinocchio"
        )
    )
    store.commit_to_store()

    # WHEN getting the sequencing run by the wrong internal_id
    # THEN an error stating that the run was not found is raised
    with pytest.raises(PacbioSequencingRunNotFoundError):
        store.get_pacbio_sequencing_run_by_internal_id("Geppetto")
