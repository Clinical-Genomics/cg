from unittest.mock import Mock, create_autospec

import pytest

from cg.server.endpoints.sequencing_run.dtos import (
    PacbioSequencingRunDTO,
    PacbioSequencingRunResponse,
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
    """Tests getting all Pacbio sequencing runs from the store."""
    # GIVEN that there are two Pacbio sequencing runs in the store
    runs = [
        create_autospec(
            PacbioSequencingRun,
            run_name="santas_little_helper",
            comment="hunden i Simpsons",
            processed=True,
        ),
        create_autospec(
            PacbioSequencingRun, run_name="Nisse", comment="Tomtens hjälpreda", processed=False
        ),
    ]
    status_db = create_autospec(Store)
    status_db.get_all_pacbio_sequencing_runs = Mock(return_value=runs)

    pacbio_sequencing_run_service = PacbioSequencingRunsService(store=status_db)

    # WHEN getting all Pacbio sequencing runs
    sequencing_runs = pacbio_sequencing_run_service.get_all_sequencing_runs()

    #
    assert sequencing_runs == PacbioSequencingRunResponse(
        pacbio_sequencing_runs=[
            PacbioSequencingRunDTO(
                run_name="santas_little_helper", comment="hunden i Simpsons", processed=True
            ),
            PacbioSequencingRunDTO(run_name="Nisse", comment="Tomtens hjälpreda", processed=False),
        ]
    )
