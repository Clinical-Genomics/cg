"""Tests for the ValidatePacBioFileTransferService class."""

from pathlib import Path

from cg.constants.file_transfer_service import PACBIO_MANIFEST_FILE_PATTERN, TRANSFER_VALIDATED_FILE
from cg.models.cg_config import CGConfig
from cg.services.validate_file_transfer_service.validate_pacbio_file_transfer_service import (
    ValidatePacbioFileTransferService,
)


def test_create_systemd_trigger_file(
    pacbio_runs_dir: Path,
    pacbio_run_id: str,
    validate_pacbio_service: ValidatePacbioFileTransferService,
    smrt_cell_id: str,
):
    """Test the create systemd trigger file method."""
    # GIVEN a manifest file

    manifest_file: Path = validate_pacbio_service.get_manifest_file_paths(
        source_dir=pacbio_runs_dir, pattern=PACBIO_MANIFEST_FILE_PATTERN
    )[0]

    # WHEN creating the systemd trigger file
    validate_pacbio_service.create_systemd_trigger_file(manifest_file_path=manifest_file)

    # THEN assert that the systemd trigger file was created
    assert Path(pacbio_runs_dir, pacbio_run_id + "-" + smrt_cell_id).exists()


def test_create_validated_transfer_file(
    pacbio_runs_dir: Path,
    pacbio_run_id: str,
    validate_pacbio_service: ValidatePacbioFileTransferService,
):
    """Test the create validated transfer file method."""
    # GIVEN a manifest file

    manifest_file: Path = validate_pacbio_service.get_manifest_file_paths(
        source_dir=pacbio_runs_dir, pattern=PACBIO_MANIFEST_FILE_PATTERN
    )[0]

    # WHEN creating the validated transfer file
    validate_pacbio_service.create_validated_transfer_file(manifest_file_path=manifest_file)

    # THEN assert that the validated transfer file was created
    assert Path(manifest_file.parent, TRANSFER_VALIDATED_FILE).exists()


def test_get_run_id(
    pacbio_runs_dir: Path,
    pacbio_run_id: str,
    validate_pacbio_service: ValidatePacbioFileTransferService,
):
    """Test the get run ID method."""
    # GIVEN a manifest file

    manifest_file: Path = validate_pacbio_service.get_manifest_file_paths(
        source_dir=pacbio_runs_dir, pattern=PACBIO_MANIFEST_FILE_PATTERN
    )[0]

    # WHEN getting the run ID
    extracted_run_id: str = validate_pacbio_service.get_run_id(manifest_file_path=manifest_file)

    # THEN it is the expected run id
    assert extracted_run_id == pacbio_run_id


def test_get_smrt_cell_id(
    pacbio_runs_dir: Path,
    smrt_cell_id: str,
    validate_pacbio_service: ValidatePacbioFileTransferService,
):
    """Test the get smrt cell ID method."""
    # GIVEN a manifest file

    manifest_file: Path = validate_pacbio_service.get_manifest_file_paths(
        source_dir=pacbio_runs_dir, pattern=PACBIO_MANIFEST_FILE_PATTERN
    )[0]

    # WHEN getting the smrt cell ID
    extracted_smrt_cell_id: str = validate_pacbio_service.get_smrt_cell_id(
        manifest_file_path=manifest_file
    )

    # THEN it is the expected smrt cell id
    assert extracted_smrt_cell_id == smrt_cell_id
