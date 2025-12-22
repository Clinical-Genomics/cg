from cg.constants.devices import RevioNames
from cg.services.run_devices.pacbio.data_transfer_service.dto import PacBioSequencingRunDTO
from cg.store.store import Store


def test_get_pacbio_sequencing_runs(
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

    # WHEN fetching the runs
    runs = store.get_pacbio_sequencing_runs()

    # THEN the two runs should be returned
    assert runs[0].run_name == "pinocchio"
    assert runs[1].run_name == "grinch"


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
    runs = store.get_pacbio_sequencing_runs(page=2, page_size=2)

    # THEN the two runs should be returned
    assert runs[0].run_name == "sauron"
    assert runs[1].run_name == "jesus_christ"
