"""Module for the Illumina encrypt run service test."""

import logging

import shutil
from pathlib import Path


import pytest

from cg.exc import IlluminaRunEncryptionError, FlowCellError
from cg.services.illumina.backup.encrypt_service import (
    IlluminaRunEncryptionService,
)
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


def test_illumina_run_encryption_service(
    illumina_run_encryption_service: IlluminaRunEncryptionService,
):
    """Tests instantiating an IlluminaRunEncryptionService."""
    # GIVEN an IlluminaRunEncryptionService

    # WHEN instantiating the service

    # THEN return a IlluminaRunEncryptionService object
    assert isinstance(illumina_run_encryption_service, IlluminaRunEncryptionService)


def test_get_run_symmetric_encryption_command(
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    output_file_path: Path,
    temporary_passphrase: Path,
):
    # GIVEN a IlluminaRunEncryptionService

    # WHEN getting the command
    command: str = illumina_run_encryption_service.get_run_symmetric_encryption_command(
        output_file=output_file_path, passphrase_file_path=temporary_passphrase
    )

    # THEN return a string
    assert isinstance(command, str)


def test_get_run_symmetric_decryption_command(
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    input_file_path: Path,
    temporary_passphrase: Path,
):
    # GIVEN a IlluminaRunEncryptionService

    # WHEN getting the command
    command: str = illumina_run_encryption_service.get_run_symmetric_decryption_command(
        input_file=input_file_path, passphrase_file_path=temporary_passphrase
    )

    # THEN return a string
    assert isinstance(command, str)


def test_create_pending_file(
    illumina_run_encryption_service: IlluminaRunEncryptionService,
):
    # GIVEN a IlluminaRunEncryptionService

    # WHEN checking if encryption is possible
    illumina_run_encryption_service.run_encryption_dir.mkdir(parents=True)
    illumina_run_encryption_service.dry_run = False
    illumina_run_encryption_service.create_pending_file(
        pending_path=illumina_run_encryption_service.pending_file_path
    )

    # THEN pending file should exist
    assert illumina_run_encryption_service.pending_file_path.exists()

    # Clean-up
    shutil.rmtree(illumina_run_encryption_service.run_encryption_dir)


def test_create_pending_file_when_dry_run(
    illumina_run_encryption_service: IlluminaRunEncryptionService,
):
    # GIVEN a IlluminaRunEncryptionService

    # WHEN checking if encryption is possible
    illumina_run_encryption_service.create_pending_file(
        pending_path=illumina_run_encryption_service.pending_file_path
    )

    # THEN pending file should not exist
    assert not illumina_run_encryption_service.pending_file_path.exists()


def test_is_encryption_possible(
    illumina_run_encryption_service: IlluminaRunEncryptionService, mocker
):
    # GIVEN a IlluminaRunEncryptionService

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # WHEN checking if encryption is possible
    is_possible: bool = illumina_run_encryption_service.is_encryption_possible()

    # THEN return True
    assert is_possible


def test_is_encryption_possible_when_sequencing_not_ready(
    caplog,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    flow_cell_name: str,
    mocker,
):
    caplog.set_level(logging.ERROR)

    # GIVEN a IlluminaRunEncryptionService

    # GIVEN that sequencing is not ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = False

    # WHEN checking if encryption is possible
    with pytest.raises(FlowCellError):
        illumina_run_encryption_service.is_encryption_possible()

        # THEN error should be raised


def test_is_encryption_possible_when_encryption_is_completed(
    caplog,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    mocker,
):
    # GIVEN a IlluminaRunEncryptionService

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # GIVEN that encryption is completed
    illumina_run_encryption_service.run_encryption_dir.mkdir(parents=True)
    illumina_run_encryption_service.complete_file_path.touch()

    # WHEN checking if encryption is possible
    with pytest.raises(IlluminaRunEncryptionError):
        illumina_run_encryption_service.is_encryption_possible()

        # THEN error should be raised

    # Clean-up
    shutil.rmtree(illumina_run_encryption_service.run_encryption_dir)


def test_is_encryption_possible_when_encryption_is_pending(
    caplog,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    mocker,
):
    # GIVEN a IlluminaRunEncryptionService

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # GIVEN that encryption is pending
    illumina_run_encryption_service.run_encryption_dir.mkdir(parents=True)
    illumina_run_encryption_service.pending_file_path.touch()

    # WHEN checking if encryption is possible
    with pytest.raises(IlluminaRunEncryptionError):
        illumina_run_encryption_service.is_encryption_possible()

        # THEN an error should be raised

    # Clean-up
    shutil.rmtree(illumina_run_encryption_service.run_encryption_dir)


def test_encrypt_run(
    caplog,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    mocker,
    sbatch_job_number: int,
):
    caplog.set_level(logging.INFO)
    # GIVEN a IlluminaRunEncryptionService

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # WHEN encrypting an Illumina run
    illumina_run_encryption_service.encrypt_run()

    # THEN sbatch should be submitted
    assert f"Run encryption running as job {sbatch_job_number}" in caplog.text


def test_start_encryption(
    caplog,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    mocker,
    sbatch_job_number: int,
):
    caplog.set_level(logging.INFO)
    # GIVEN a IlluminaRunEncryptionService

    # GIVEN that sequencing is ready
    mocker.patch.object(IlluminaRunDirectoryData, "is_sequencing_run_ready")
    IlluminaRunDirectoryData.is_sequencing_run_ready.return_value = True

    # WHEN trying to start encrypting an Illumina run
    illumina_run_encryption_service.start_encryption()

    # THEN sbatch should be submitted
    assert f"Run encryption running as job {sbatch_job_number}" in caplog.text
