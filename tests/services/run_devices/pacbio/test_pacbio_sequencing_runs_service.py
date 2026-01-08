from unittest.mock import Mock, create_autospec

import pytest

from cg.server.endpoints.sequencing_run.dtos import (
    PacbioSequencingRunDTO,
    PacbioSequencingRunResponse,
    PacbioSequencingRunUpdateRequest,
    PacbioSmrtCellMetricsResponse,
)
from cg.services.run_devices.pacbio.sequencing_runs_service import PacbioSequencingRunsService
from cg.store.exc import EntryNotFoundError
from cg.store.models import PacbioSequencingRun, PacbioSMRTCellMetrics
from cg.store.store import Store


def test_get_pacbio_sequencing_runs_by_name(
    pacbio_sequencing_runs_service: PacbioSequencingRunsService, pacbio_run_name_to_fetch: str
):
    """Tests getting Pacbio sequencing runs from the store filtered on run name."""

    # GIVEN that there are multiple Pacbio sequencing runs with different run names
    all_runs: list[PacbioSMRTCellMetrics] = pacbio_sequencing_runs_service.store._get_query(
        table=PacbioSMRTCellMetrics
    ).all()
    assert any(run.run_name != pacbio_run_name_to_fetch for run in all_runs)

    # WHEN fetching sequencing runs filtered by run name
    runs: PacbioSmrtCellMetricsResponse = (
        pacbio_sequencing_runs_service.get_sequencing_runs_by_name(pacbio_run_name_to_fetch)
    )

    # THEN all the returned runs have the correct run name
    assert all(run.run_name == pacbio_run_name_to_fetch for run in runs.runs)


def test_get_pacbio_sequencing_runs_by_name_no_matches(
    pacbio_sequencing_runs_service: PacbioSequencingRunsService,
):
    """Tests getting Pacbio runs from the store filtered on a non-existent run name."""

    # GIVEN that there are no Pacbio sequencing runs with a specific run name
    all_runs: list[PacbioSMRTCellMetrics] = pacbio_sequencing_runs_service.store._get_query(
        table=PacbioSMRTCellMetrics
    ).all()
    assert all(run.run_name != "Non-existent run" for run in all_runs)

    # WHEN fetching sequencing runs filtered by run name

    # THEN an EntryNotFoundError should be raised when trying to get sequencing runs filtered on that name
    with pytest.raises(EntryNotFoundError):
        pacbio_sequencing_runs_service.get_sequencing_runs_by_name("Non-existent run")


def test_get_all_pacbio_sequencing_runs():
    # GIVEN that there are two PacBio sequencing runs in the store
    runs = [
        create_autospec(
            PacbioSequencingRun,
            id=6,
            run_name="santas_little_helper",
            comment="hunden i Simpsons",
            processed=True,
        ),
        create_autospec(
            PacbioSequencingRun,
            id=4,
            run_name="Nisse",
            comment="Tomtens hjälpreda",
            processed=False,
        ),
    ]
    status_db: Store = create_autospec(Store)
    status_db.get_pacbio_sequencing_runs = Mock(return_value=(runs, 2))

    # GIVEN a PacBio sequencing run service
    pacbio_sequencing_run_service = PacbioSequencingRunsService(store=status_db)

    # WHEN getting all PacBio sequencing runs
    sequencing_runs: PacbioSequencingRunResponse = (
        pacbio_sequencing_run_service.get_sequencing_runs()
    )

    # THEN all PacBio sequencing run are returned
    assert sequencing_runs == PacbioSequencingRunResponse(
        pacbio_sequencing_runs=[
            PacbioSequencingRunDTO(
                id=6, run_name="santas_little_helper", comment="hunden i Simpsons", processed=True
            ),
            PacbioSequencingRunDTO(
                id=4, run_name="Nisse", comment="Tomtens hjälpreda", processed=False
            ),
        ],
        total_count=2,
    )


def test_get_sequencing_runs_with_pagination():
    # GIVEN a store
    status_db = create_autospec(Store)
    status_db.get_pacbio_sequencing_runs = Mock(return_value=([], 0))

    # GIVEN a PacBio sequencing run service
    pacbio_sequencing_run_service = PacbioSequencingRunsService(store=status_db)

    # WHEN passing page and page_size to the method
    pacbio_sequencing_run_service.get_sequencing_runs(page=5, page_size=50)

    # THEN the method should be called with these arguments
    status_db.get_pacbio_sequencing_runs.assert_called_once_with(page=5, page_size=50)


def test_update_sequencing_run():
    # GIVEN a store
    status_db = create_autospec(Store)

    # GIVEN an incoming request with comment and processed set
    update_request = PacbioSequencingRunUpdateRequest(id=1, comment="", processed=False)

    # GIVEN a PacBio sequencing run service
    pacbio_sequencing_run_service = PacbioSequencingRunsService(store=status_db)

    # WHEN updating a sequencing run
    pacbio_sequencing_run_service.update_sequencing_run(update_request=update_request)

    # THEN the fields in the sequencing run are updated
    status_db.update_pacbio_sequencing_run_comment.assert_called_once_with(
        id=update_request.id, comment=update_request.comment
    )
    status_db.update_pacbio_sequencing_run_processed.assert_called_once_with(
        id=update_request.id, processed=update_request.processed
    )


def test_update_sequencing_run_only_processed():
    # GIVEN a store
    status_db = create_autospec(Store)

    # GIVEN an incoming request with only processed set
    update_request = PacbioSequencingRunUpdateRequest(id=1, processed=True)

    # GIVEN a PacBio sequencing run service
    pacbio_sequencing_run_service = PacbioSequencingRunsService(store=status_db)

    # WHEN updating a sequencing run
    pacbio_sequencing_run_service.update_sequencing_run(update_request=update_request)

    # THEN only processed is updated
    status_db.update_pacbio_sequencing_run_comment.assert_not_called()
    status_db.update_pacbio_sequencing_run_processed.assert_called_once_with(
        id=update_request.id, processed=update_request.processed
    )
