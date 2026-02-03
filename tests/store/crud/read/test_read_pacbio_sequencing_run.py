import pytest

from cg.constants.devices import RevioNames
from cg.exc import PacbioSequencingRunNotFoundError
from cg.services.run_devices.pacbio.data_transfer_service.dto import PacBioSequencingRunDTO
from cg.store.models import PacbioSequencingRun
from cg.store.store import Store


@pytest.fixture
def pacbio_sequencing_run_dto() -> PacBioSequencingRunDTO:
    return PacBioSequencingRunDTO(
        instrument_name=RevioNames.BETTY,
        run_id="pinocchio",
        run_name="run-name",
        unique_id="unique-id",
    )


def test_get_pacbio_sequencing_runs(
    store: Store,
):
    # GIVEN a store with two runs
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY,
            run_id="r_older",
            run_name="run-name-older",
            unique_id="unique-id-older",
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.WILMA,
            run_id="r_newer",
            run_name="run-name-newer",
            unique_id="unique-id-newer",
        )
    )

    # WHEN fetching the runs
    runs, total_count = store.get_pacbio_sequencing_runs()

    # THEN the two runs should be returned
    assert runs[0].run_id == "r_newer"
    assert runs[1].run_id == "r_older"
    assert total_count == 2


def test_get_pacbio_sequencing_runs_with_pagination(
    store: Store,
):
    # GIVEN a store with four runs
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY,
            run_id="pinocchio",
            run_name="run-name-1",
            unique_id="unique-id-1",
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.WILMA,
            run_id="grinch",
            run_name="run-name-2",
            unique_id="unique-id-2",
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.BETTY,
            run_id="sauron",
            run_name="run-name-3",
            unique_id="unique-id-3",
        )
    )
    store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto=PacBioSequencingRunDTO(
            instrument_name=RevioNames.WILMA,
            run_id="jesus_christ",
            run_name="run-name-4",
            unique_id="unique-id-4",
        )
    )

    # WHEN fetching the second page of runs with page size two
    runs, total_count = store.get_pacbio_sequencing_runs(page=2, page_size=2)

    # THEN the two runs should be returned
    assert runs[0].run_id == "grinch"
    assert runs[1].run_id == "pinocchio"
    assert total_count == 4


def test_get_pacbio_sequencing_run_by_id_successful(
    store: Store, pacbio_sequencing_run_dto: PacBioSequencingRunDTO
):
    # GIVEN a store with a Pacbio sequencing run
    sequencing_run: PacbioSequencingRun = store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto
    )
    store.commit_to_store()

    # WHEN getting the sequencing run by id
    fetched_run: PacbioSequencingRun = store.get_pacbio_sequencing_run_by_id(sequencing_run.id)

    # THEN the fetched run is as expected
    assert fetched_run == sequencing_run


def test_get_pacbio_sequencing_run_by_id_unsuccessful(
    store: Store, pacbio_sequencing_run_dto: PacBioSequencingRunDTO
):
    # GIVEN a store with a Pacbio sequencing run
    sequencing_run: PacbioSequencingRun = store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto
    )
    store.commit_to_store()

    # WHEN getting the sequencing run by the wrong id
    # THEN an error stating that the run was not found is raised
    with pytest.raises(PacbioSequencingRunNotFoundError):
        store.get_pacbio_sequencing_run_by_id(sequencing_run.id + 1)


def test_get_pacbio_sequencing_run_by_run_name_successful(
    store: Store, pacbio_sequencing_run_dto: PacBioSequencingRunDTO
):
    # GIVEN a store with a Pacbio sequencing run
    sequencing_run: PacbioSequencingRun = store.create_pacbio_sequencing_run(
        pacbio_sequencing_run_dto
    )
    store.commit_to_store()

    # WHEN getting the sequencing run by run ID
    fetched_run: PacbioSequencingRun = store.get_pacbio_sequencing_run_by_run_id(
        sequencing_run.run_id
    )

    # THEN the fetched run is as expected
    assert fetched_run == sequencing_run


def test_get_pacbio_sequencing_run_by_run_name_unsuccessful(
    store: Store, pacbio_sequencing_run_dto: PacBioSequencingRunDTO
):
    # GIVEN a store with a Pacbio sequencing run
    store.create_pacbio_sequencing_run(pacbio_sequencing_run_dto)
    store.commit_to_store()

    # WHEN getting the sequencing run by the wrong run ID
    # THEN an error stating that the run was not found is raised
    with pytest.raises(PacbioSequencingRunNotFoundError):
        store.get_pacbio_sequencing_run_by_run_id("Geppetto")
