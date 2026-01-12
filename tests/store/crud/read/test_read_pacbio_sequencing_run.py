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
            instrument_name=RevioNames.BETTY, run_name="older"
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.WILMA, run_name="newer"
        )
    )

    # WHEN fetching the runs
    runs, total_count = store.get_pacbio_sequencing_runs()

    # THEN the two runs should be returned
    assert runs[0].run_name == "newer"
    assert runs[1].run_name == "older"
    assert total_count == 2


def test_get_pacbio_sequencing_runs_with_pagination(
    store: Store,
):
    # GIVEN a store with two runs
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, run_name="pinocchio"
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.WILMA, run_name="grinch"
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, run_name="sauron"
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.WILMA, run_name="jesus_christ"
        )
    )

    # WHEN fetching the runs
    runs, total_count = store.get_pacbio_sequencing_runs(page=2, page_size=2)

    # THEN the two runs should be returned
    assert runs[0].run_name == "grinch"
    assert runs[1].run_name == "pinocchio"
    assert total_count == 4


def test_get_pacbio_sequencing_run_by_id_successful(store: Store):
    # GIVEN a store with a Pacbio sequencing run
    sequencing_run: PacbioSequencingRun = store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, run_name="pinocchio"
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
            instrument_name=RevioNames.BETTY, run_name="pinocchio"
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
            instrument_name=RevioNames.BETTY, run_name="pinocchio"
        )
    )
    store.commit_to_store()

    # WHEN getting the sequencing run by run_name
    fetched_run: PacbioSequencingRun = store.get_pacbio_sequencing_run_by_run_name(
        sequencing_run.run_name
    )

    # THEN the fetched run is as expected
    assert fetched_run == sequencing_run


def test_get_pacbio_sequencing_run_by_run_name_unsuccessful(store: Store):
    # GIVEN a store with a Pacbio sequencing run
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY, run_name="pinocchio"
        )
    )
    store.commit_to_store()

    # WHEN getting the sequencing run by the wrong run_name
    # THEN an error stating that the run was not found is raised
    with pytest.raises(PacbioSequencingRunNotFoundError):
        store.get_pacbio_sequencing_run_by_run_name("Geppetto")
