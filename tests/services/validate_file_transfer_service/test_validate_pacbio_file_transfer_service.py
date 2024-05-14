"""Tests for the ValidatePacBioFileTransferService class."""

from pathlib import Path

from cg.models.cg_config import CGConfig
from cg.services.validate_file_transfer_service.validate_pacbio_file_transfer_service import (
    ValidatePacbioFileTransferService,
)


def test_get_run_ids(cg_context: CGConfig, pacbio_runs_dir: Path, pacbio_run_id: str):
    """Test getting Pacbio run ids."""

    # GIVEN a directory with Pacbio runs as subdirectories
    validate_pacbio_file_transfer_service = ValidatePacbioFileTransferService(config=cg_context)
    validate_pacbio_file_transfer_service.data_dir = pacbio_runs_dir

    # WHEN getting the Pacbio run ids
    run_ids: list[str] = validate_pacbio_file_transfer_service.get_run_ids()

    # THEN assert that the Pacbio run ids are returned
    assert len(run_ids) == 1
    assert run_ids[0] == pacbio_run_id
