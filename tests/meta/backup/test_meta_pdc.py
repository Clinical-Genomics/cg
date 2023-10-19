"""Tests for the meta PdcAPI"""
from unittest import mock

import pytest

from cg.exc import (
    DcmsAlreadyRunningError,
    FlowCellAlreadyBackedUpError,
    FlowCellEncryptionError,
)
from cg.meta.backup.pdc import PdcAPI
from cg.meta.encryption.encryption import FlowCellEncryptionAPI
from cg.store import Store
from cg.store.models import Flowcell
from tests.store_helpers import StoreHelpers


def test_validate_is_dcms_process_running(binary_path: str):
    """Tests checking if a Dcms process is running when no Dcms process is running."""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)

    # WHEN checking if Dcms is running
    is_dmsc_running: bool = pdc_api.validate_is_dcms_running()

    # THEN return false
    assert not is_dmsc_running


def test_validate_is_flow_cell_backup_possible(
    base_store: Store,
    binary_path: str,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
):
    """Tests checking if a back-up of flow-cell is possible."""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)

    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=flow_cell_encryption_api.flow_cell.id,
        store=base_store,
    )

    # GIVEN that encryption is completed
    flow_cell_encryption_api.flow_cell_encryption_dir.mkdir(parents=True)
    flow_cell_encryption_api.complete_file_path.touch()

    # WHEN checking if back-up is possible
    is_backup_possible: bool = pdc_api.validate_is_flow_cell_backup_possible(
        db_flow_cell=db_flow_cell, flow_cell_encryption_api=flow_cell_encryption_api
    )

    # THEN return true
    assert is_backup_possible


def test_validate_is_flow_cell_backup_when_dcms_is_already_running(
    base_store: Store,
    binary_path: str,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
    mocker,
):
    """Tests checking if a back-up of flow-cell is possible."""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)

    # GIVEN a Dcms process is already running
    mocker.patch.object(PdcAPI, "validate_is_dcms_running", return_value=True)

    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=flow_cell_encryption_api.flow_cell.id,
        store=base_store,
    )

    # WHEN checking if back-up is possible
    with pytest.raises(DcmsAlreadyRunningError):
        pdc_api.validate_is_flow_cell_backup_possible(
            db_flow_cell=db_flow_cell, flow_cell_encryption_api=flow_cell_encryption_api
        )

        # THEN error should be raised


def test_validate_is_flow_cell_backup_when_already_backed_up(
    base_store: Store,
    binary_path: str,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
):
    """Tests checking if a back-up of flow-cell is possible."""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)

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


def test_validate_is_flow_cell_backup_when_encryption_is_not_completee(
    base_store: Store,
    binary_path: str,
    helpers: StoreHelpers,
    flow_cell_encryption_api: FlowCellEncryptionAPI,
):
    """Tests checking if a back-up of flow-cell is possible."""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)

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


@mock.patch("cg.meta.backup.pdc.Process")
def test_archive_file_to_pdc(mock_process, binary_path, backup_file_path):
    """Tests execution command to archive file to PDC"""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)
    pdc_api.process = mock_process

    # WHEN archiving a file to PDC
    pdc_api.archive_file_to_pdc(backup_file_path)

    # THEN a dsmc process should be started with the parameter 'archive'
    mock_process.run_command.assert_called_once_with(
        parameters=["archive", backup_file_path], dry_run=False
    )


@mock.patch("cg.meta.backup.pdc.Process")
def test_query_pdc(mock_process, binary_path, backup_file_path):
    """Tests execution command to query files to PDC"""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)
    pdc_api.process = mock_process

    # WHEN querying PDC
    pdc_api.query_pdc(backup_file_path)

    # THEN a dsmc process should be started with parameters 'q archive'
    mock_process.run_command.assert_called_once_with(parameters=["q", "archive", backup_file_path])


@mock.patch("cg.meta.backup.pdc.Process")
def test_retrieve_file_from_pdc(mock_process, binary_path, backup_file_path):
    """Tests execution command to retrieve files from PDC"""
    # GIVEN an instance of the PDC API
    pdc_api = PdcAPI(binary_path=binary_path)
    pdc_api.process = mock_process

    # WHEN retrieving a file form PDC
    pdc_api.retrieve_file_from_pdc(backup_file_path)

    # THEN a dsmc process should be started with parameters 'retrieve -replace=yes'
    mock_process.run_command.assert_called_once_with(
        parameters=["retrieve", "-replace=yes", backup_file_path], dry_run=False
    )
