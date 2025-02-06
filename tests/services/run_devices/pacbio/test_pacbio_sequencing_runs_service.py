from cg.server.endpoints.sequencing_run.dtos import PacbioSequencingRunsResponse
from cg.services.run_devices.pacbio.sequencing_runs_service import PacbioSequencingRunsService
from cg.store.models import PacbioSequencingRun


def test_get_pacbio_sequencing_runs_by_name(
    pacbio_sequencing_runs_service: PacbioSequencingRunsService, pacbio_run_name_to_fetch: str
):
    """Tests getting Pacbio sequencing runs from the store filtered on run name."""

    # GIVEN that there are multiple Pacbio sequencing runs with different run names
    all_runs: list[PacbioSequencingRun] = pacbio_sequencing_runs_service.store._get_query(
        table=PacbioSequencingRun
    ).all()
    assert any(run.run_name != pacbio_run_name_to_fetch for run in all_runs)

    # WHEN fetching sequencing runs filtered by run name
    runs: PacbioSequencingRunsResponse = pacbio_sequencing_runs_service.get_sequencing_runs_by_name(
        pacbio_run_name_to_fetch
    )

    # THEN all the returned runs have the correct run name
    assert all(run.run_name == pacbio_run_name_to_fetch for run in runs.runs)
