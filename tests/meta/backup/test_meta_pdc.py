"""Tests for the meta PdcAPI"""
import logging
from unittest import mock

import pytest

from cg.exc import (
    DsmcAlreadyRunningError,
    FlowCellAlreadyBackedUpError,
    FlowCellEncryptionError,
)
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import FlowCellEncryptionAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.store.models import Flowcell
from tests.store_helpers import StoreHelpers


def test_validate_is_dsmc_process_running(cg_context: CGConfig, binary_path: str):
    """Tests checking if a Dsmc process is running when no Dsmc process is running."""
    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api

    # GIVEN no Dsmc process is running

    # WHEN checking if Dsmc is running
    is_dmsc_running: bool = pdc_api.validate_is_dsmc_running()

    # THEN return false
    assert not is_dmsc_running


def test_validate_is_flow_cell_backup_possible(
    base_store: Store,
    caplog,
    cg_context: CGConfig,
    binary_path: str,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
):
    """Tests checking if a back-up of flow-cell is possible."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api

    # GIVEN no Dsmc process is running

    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=flow_cell_encryption_api.flow_cell.id,
        store=base_store,
    )

    # GIVEN that encryption is completed
    flow_cell_encryption_api.flow_cell_encryption_dir.mkdir(parents=True)
    flow_cell_encryption_api.complete_file_path.touch()

    # WHEN checking if back-up is possible
    pdc_api.validate_is_flow_cell_backup_possible(
        db_flow_cell=db_flow_cell, flow_cell_encryption_api=flow_cell_encryption_api
    )

    # THEN communicate that it passed
    assert "Flow cell can be backed up" in caplog.text


def test_validate_is_flow_cell_backup_when_dsmc_is_already_running(
    base_store: Store,
    cg_context: CGConfig,
    binary_path: str,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
    mocker,
):
    """Tests checking if a back-up of flow-cell is possible when Dsmc is already running."""
    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api

    # GIVEN a Dsmc process is already running
    mocker.patch.object(PdcAPI, "validate_is_dsmc_running", return_value=True)

    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=flow_cell_encryption_api.flow_cell.id,
        store=base_store,
    )

    # WHEN checking if back-up is possible
    with pytest.raises(DsmcAlreadyRunningError):
        pdc_api.validate_is_flow_cell_backup_possible(
            db_flow_cell=db_flow_cell, flow_cell_encryption_api=flow_cell_encryption_api
        )

        # THEN error should be raised


def test_validate_is_flow_cell_backup_when_already_backed_up(
    base_store: Store,
    cg_context: CGConfig,
    binary_path: str,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
):
    """Tests checking if a back-up of flow-cell is possible when flow cell is already backed up."""
    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api

    # GIVEN a database flow cell which is backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=flow_cell_encryption_api.flow_cell.id, store=base_store, has_backup=True
    )

    # WHEN checking if back-up is possible
    with pytest.raises(FlowCellAlreadyBackedUpError):
        pdc_api.validate_is_flow_cell_backup_possible(
            db_flow_cell=db_flow_cell, flow_cell_encryption_api=flow_cell_encryption_api
        )

        # THEN error should be raised


def test_validate_is_flow_cell_backup_when_encryption_is_not_complete(
    base_store: Store,
    cg_context: CGConfig,
    binary_path: str,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
):
    """Tests checking if a back-up of flow-cell is possible when encryption is not complete."""
    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api

    # GIVEN a database flow cell which is backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=flow_cell_encryption_api.flow_cell.id,
        store=base_store,
    )

    # WHEN checking if back-up is possible
    with pytest.raises(FlowCellEncryptionError):
        pdc_api.validate_is_flow_cell_backup_possible(
            db_flow_cell=db_flow_cell, flow_cell_encryption_api=flow_cell_encryption_api
        )

        # THEN error should be raised


def test_backup_flow_cell(
    base_store: Store,
    cg_context: CGConfig,
    binary_path: str,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
    mocker,
):
    """Tests back-up flow cell."""
    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api

    # GIVEN a mocked archiving call
    mocker.patch.object(PdcAPI, "archive_file_to_pdc", return_value=None)

    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=flow_cell_encryption_api.flow_cell.id,
        store=base_store,
    )

    # WHEN backing up flow cell
    pdc_api.backup_flow_cell(
        files_to_archive=[
            flow_cell_encryption_api.final_passphrase_file_path,
            flow_cell_encryption_api.encrypted_gpg_file_path,
        ],
        store=base_store,
        db_flow_cell=db_flow_cell,
    )

    # THEN flow cell should hava a back-up
    assert db_flow_cell.has_backup


def test_backup_flow_cell_when_unable_to_archive(
    base_store: Store,
    binary_path: str,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
    caplog,
):
    """Tests back-up flow cell when unable to archive."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api

    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=flow_cell_encryption_api.flow_cell.id,
        store=base_store,
    )

    # WHEN backing up flow cell
    pdc_api.backup_flow_cell(
        files_to_archive=[
            flow_cell_encryption_api.final_passphrase_file_path,
            flow_cell_encryption_api.encrypted_gpg_file_path,
        ],
        store=base_store,
        db_flow_cell=db_flow_cell,
    )

    # THEN log unable to archive
    assert (
        f"{flow_cell_encryption_api.encrypted_gpg_file_path.as_posix()} cannot be archived"
        in caplog.text
    )


@mock.patch("cg.meta.backup.pdc.Process")
def test_archive_file_to_pdc(mock_process, cg_context: CGConfig, binary_path, backup_file_path):
    """Tests execution command to archive file to PDC"""
    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api
    pdc_api.process = mock_process

    # WHEN archiving a file to PDC
    pdc_api.archive_file_to_pdc(backup_file_path)

    # THEN a dsmc process should be started with the parameter 'archive'
    mock_process.run_command.assert_called_once_with(
        parameters=["archive", backup_file_path], dry_run=False
    )


@mock.patch("cg.meta.backup.pdc.Process")
def test_query_pdc(mock_process, cg_context: CGConfig, binary_path, backup_file_path):
    """Tests execution command to query files to PDC"""
    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api
    pdc_api.process = mock_process

    # WHEN querying PDC
    pdc_api.query_pdc(backup_file_path)

    # THEN a dsmc process should be started with parameters 'q archive'
    mock_process.run_command.assert_called_once_with(parameters=["q", "archive", backup_file_path])


@mock.patch("cg.meta.backup.pdc.Process")
def test_retrieve_file_from_pdc(mock_process, cg_context: CGConfig, binary_path, backup_file_path):
    """Tests execution command to retrieve files from PDC"""
    # GIVEN an instance of the PDC API
    pdc_api = cg_context.pdc_api
    pdc_api.process = mock_process

    # WHEN retrieving a file form PDC
    pdc_api.retrieve_file_from_pdc(backup_file_path)

    # THEN a dsmc process should be started with parameters 'retrieve -replace=yes'
    mock_process.run_command.assert_called_once_with(
        parameters=["retrieve", "-replace=yes", backup_file_path], dry_run=False
    )
