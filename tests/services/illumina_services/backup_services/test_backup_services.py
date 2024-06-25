"""Tests for the meta BackupAPI."""

import fnmatch
import logging
from pathlib import Path
from typing import Callable

import mock
import pytest
from cg.constants import FileExtensions, FlowCellStatus, EXIT_FAIL
from cg.constants.sequencing import Sequencers
from cg.exc import (
    DsmcAlreadyRunningError,
    FlowCellAlreadyBackedUpError,
    PdcError,
    IlluminaRunEncryptionError,
)

from cg.services.illumina_services.backup_services.backup_service import IlluminaBackupService
from cg.services.pdc_service.pdc_service import PdcService
from cg.services.illumina_services.backup_services.encrypt_service import (
    IlluminaRunEncryptionService,
)
from cg.models.cg_config import PDCArchivingDirectory, CGConfig

from cg.store.models import Flowcell
from cg.store.store import Store
from tests.conftest import create_process_response

from tests.store_helpers import StoreHelpers


@pytest.mark.parametrize(
    "flow_cell_name",
    ["new_flow_cell", "old_flow_cell", "ancient_flow_cell"],
)
def test_query_pdc_for_flow_cell(
    caplog,
    flow_cell_name: str,
    mock_pdc_query_method: Callable,
    pdc_archiving_directory: PDCArchivingDirectory,
):
    """Tests query PDC for a flow cell with a mock PDC query."""
    caplog.set_level(logging.DEBUG)

    # GIVEN a Backup API
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=pdc_archiving_directory,
        status=mock.Mock(),
        tar_api=mock.Mock(),
        pdc_service=mock.Mock(),
        flow_cells_dir=mock.Mock(),
    )
    # GIVEN a mock pdc query method
    backup_api.pdc.query_pdc = mock_pdc_query_method

    # WHEN querying pdc for a flow cell
    backup_api.query_pdc_for_flow_cell(flow_cell_id=flow_cell_name)

    # THEN the flow cell is logged as found for one of the search patterns
    assert fnmatch.filter(
        names=caplog.messages, pat=f"Found archived files for PDC query:*{flow_cell_name}*.gpg"
    )


def test_get_archived_encryption_key_path(dsmc_q_archive_output: list[str], flow_cell_name: str):
    """Tests returning an encryption key path from DSMC output."""
    # GIVEN an DSMC output and a flow cell id

    # GIVEN a Backup API
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=mock.Mock(),
        status=mock.Mock(),
        tar_api=mock.Mock(),
        pdc_service=mock.Mock(),
        flow_cells_dir=mock.Mock(),
    )

    # WHEN getting the encryption key path
    key_path: Path = backup_api.get_archived_encryption_key_path(dsmc_output=dsmc_q_archive_output)

    # THEN this method should return a path object
    assert isinstance(key_path, Path)

    # THEN return the key file name
    assert (
        key_path.name
        == f"190329_A00689_0018_A{flow_cell_name}{FileExtensions.KEY}{FileExtensions.GPG}"
    )


def test_get_archived_flow_cell_path(dsmc_q_archive_output: list[str], flow_cell_name: str):
    """Tests returning a flow cell path from DSMC output."""
    # GIVEN an DSMC output and a flow cell id

    # GIVEN a Backup API
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=mock.Mock(),
        status=mock.Mock(),
        tar_api=mock.Mock(),
        pdc_service=mock.Mock(),
        flow_cells_dir=mock.Mock(),
    )

    # WHEN getting the flow cell path
    flow_cell_path: Path = backup_api.get_archived_flow_cell_path(dsmc_output=dsmc_q_archive_output)

    # THEN this method should return a path object
    assert isinstance(flow_cell_path, Path)

    # THEN return the flow cell file name
    assert (
        flow_cell_path.name
        == f"190329_A00689_0018_A{flow_cell_name}{FileExtensions.TAR}{FileExtensions.GZIP}{FileExtensions.GPG}"
    )


@mock.patch("cg.store.store.Store")
def test_maximum_processing_queue_full(mock_store):
    """Tests check_processing method of the backup API"""
    # GIVEN a flow cell needs to be retrieved from PDC
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_service=mock.Mock(),
        flow_cells_dir=mock.Mock(),
    )

    # WHEN there's already a flow cell being retrieved from PDC
    mock_store.get_flow_cells_by_statuses.return_value = [[mock.Mock()]]

    # THEN this method should return False
    assert backup_api.check_processing() is False


@mock.patch("cg.store")
def test_maximum_processing_queue_not_full(mock_store):
    """Tests check_processing method of the backup API"""
    # GIVEN a flow cell needs to be retrieved from PDC
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_service=mock.Mock(),
        flow_cells_dir=mock.Mock(),
    )
    # WHEN there are no flow cells being retrieved from PDC
    mock_store.get_flow_cells_by_statuses().return_value = []

    # THEN this method should return True
    assert backup_api.check_processing() is True


@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.store")
def test_get_first_flow_cell_next_requested(mock_store, mock_flow_cell):
    """Tests get_first_flow_cell method of the backup API when requesting next flow cell"""
    # GIVEN status-db needs to be checked for flow cells to be retrieved from PDC
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_service=mock.Mock(),
        flow_cells_dir=mock.Mock(),
    )

    # WHEN a flow cell is requested to be retrieved from PDC
    mock_store.get_flow_cells_by_statuses().return_value = [mock_flow_cell]

    popped_flow_cell = backup_api.get_first_flow_cell()

    # THEN a flow cell is returned
    assert popped_flow_cell is not None


@mock.patch("cg.store")
def test_get_first_flow_cell_no_flow_cell_requested(mock_store):
    """Tests get_first_flow_cell method of the backup API when no flow cell requested"""
    # GIVEN status-db needs to be checked for flow cells to be retrieved from PDC
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_service=mock.Mock(),
        flow_cells_dir=mock.Mock(),
    )

    # WHEN there are no flow cells requested to be retrieved from PDC
    mock_store.get_flow_cells_by_statuses.return_value = []

    popped_flow_cell = backup_api.get_first_flow_cell()

    # THEN no flow cell is returned
    assert popped_flow_cell is None


@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.check_processing"
)
@mock.patch("cg.store.models.Flowcell")
def test_fetch_flow_cell_processing_queue_full(mock_flow_cell, mock_check_processing, caplog):
    """Tests the fetch_flow_cell method of the backup API when processing queue is full"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flow cell needs to be retrieved from PDC
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=mock.Mock(),
        status=mock.Mock(),
        tar_api=mock.Mock(),
        pdc_service=mock.Mock(),
        flow_cells_dir=mock.Mock(),
    )

    # WHEN the processing queue is full
    backup_api.check_processing.return_value = False
    result = backup_api.fetch_flow_cell(mock_flow_cell)

    # THEN no flow cell will be fetched and a log message indicates that the processing queue is
    # full
    assert result is None
    assert "Processing queue is full" in caplog.text


@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.get_first_flow_cell"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.check_processing"
)
@mock.patch("cg.store")
def test_fetch_flow_cell_no_flow_cells_requested(
    mock_store,
    mock_check_processing,
    mock_get_first_flow_cell,
    caplog,
):
    """Tests the fetch_flow_cell method of the backup API when no flow cell requested"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flow cell needs to be retrieved from PDC
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=mock.Mock(),
        status=mock_store,
        tar_api=mock.Mock(),
        pdc_service=mock.Mock(),
        flow_cells_dir=mock.Mock(),
    )

    # WHEN no flow cells are requested
    backup_api.get_first_flow_cell.return_value = None
    backup_api.check_processing.return_value = True

    # AND no flow cell has been specified
    mock_flow_cell = None

    result = backup_api.fetch_flow_cell(mock_flow_cell)

    # THEN no flow cell will be fetched and a log message indicates that no flow cells have been
    # requested
    assert result is None
    assert "No flow cells requested" in caplog.text


@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.unlink_files"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.create_rta_complete"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.create_copy_complete"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.get_archived_flow_cell_path"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.get_archived_encryption_key_path"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.check_processing"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.get_first_flow_cell"
)
@mock.patch("cg.meta.tar.tar.TarAPI")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.store")
def test_fetch_flow_cell_retrieve_next_flow_cell(
    mock_store,
    mock_flow_cell,
    mock_tar,
    mock_get_first_flow_cell,
    mock_get_archived_encryption_key_path,
    mock_get_archived_flow_cell_path,
    mock_create_copy_complete,
    mock_create_rta_complete,
    archived_key,
    archived_flow_cell,
    cg_context,
    caplog,
):
    """Tests the fetch_flow_cell method of the backup API when retrieving next flow cell"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flow cell needs to be retrieved from PDC
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status=mock_store,
        tar_api=mock_tar,
        pdc_service=mock.Mock(),
        flow_cells_dir="cg_context.flow_cells_dir",
    )

    # WHEN no flow cell is specified, but a flow cell in status-db has the status "requested"
    mock_flow_cell.status = FlowCellStatus.REQUESTED
    mock_flow_cell.sequencer_type = Sequencers.NOVASEQ
    backup_api.get_first_flow_cell.return_value = mock_flow_cell
    backup_api.check_processing.return_value = True
    backup_api.get_archived_encryption_key_path.return_value = archived_key
    backup_api.get_archived_flow_cell_path.return_value = archived_flow_cell
    backup_api.tar_api.run_tar_command.return_value = None
    result = backup_api.fetch_flow_cell(flow_cell=None)

    # THEN the process to retrieve the flow cell from PDC is started
    assert "retrieving from PDC" in caplog.text

    # AND when done the status of that flow cell is set to "retrieved"
    assert (
        f"Status for flow cell {mock_get_first_flow_cell.return_value.name} set to "
        f"{FlowCellStatus.RETRIEVED}" in caplog.text
    )
    assert mock_flow_cell.status == "retrieved"

    # AND status-db is updated with the new status
    assert mock_store.session.commit.called

    # AND the elapsed time of the retrieval process is returned
    assert result > 0


@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.unlink_files"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.create_rta_complete"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.create_copy_complete"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.get_archived_flow_cell_path"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.get_archived_encryption_key_path"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.check_processing"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.get_first_flow_cell"
)
@mock.patch("cg.meta.tar.tar.TarAPI")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.store")
def test_fetch_flow_cell_retrieve_specified_flow_cell(
    mock_store,
    mock_flow_cell,
    mock_tar,
    mock_get_first_flow_cell,
    mock_check_processing,
    mock_get_archived_key,
    mock_get_archived_flow_cell,
    mock_create_copy_complete,
    mock_create_rta_complete,
    mock_unlink_files,
    archived_key,
    archived_flow_cell,
    cg_context,
    caplog,
):
    """Tests the fetch_flow_cell method of the backup API when given a flow cell"""

    caplog.set_level(logging.INFO)

    # GIVEN we want to retrieve a specific flow cell from PDC
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status=mock_store,
        tar_api=mock_tar,
        pdc_service=mock.Mock(),
        flow_cells_dir="cg_context.flow_cells_dir",
    )
    mock_flow_cell.status = FlowCellStatus.REQUESTED
    mock_flow_cell.sequencer_type = Sequencers.NOVASEQ
    backup_api.check_processing.return_value = True
    backup_api.get_archived_encryption_key_path.return_value = archived_key
    backup_api.get_archived_flow_cell_path.return_value = archived_flow_cell
    backup_api.tar_api.run_tar_command.return_value = None
    result = backup_api.fetch_flow_cell(flow_cell=mock_flow_cell)

    # THEN no flow cell is taken form statusdb
    mock_get_first_flow_cell.assert_not_called()

    # THEN the process to retrieve the flow cell from PDC is started
    assert "retrieving from PDC" in caplog.text

    # AND when done the status of that flow cell is set to "retrieved"
    assert (
        f"Status for flow cell {mock_flow_cell.name} set to {FlowCellStatus.RETRIEVED}"
        in caplog.text
    )
    assert mock_flow_cell.status == "retrieved"

    # AND status-db is updated with the new status
    assert mock_store.session.commit.called

    # AND the elapsed time of the retrieval process is returned
    assert result > 0


@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.unlink_files"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.create_rta_complete"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.create_copy_complete"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.query_pdc_for_flow_cell"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.get_archived_encryption_key_path"
)
@mock.patch(
    "cg.services.illumina_services.backup_services.backup_service.IlluminaBackupService.get_archived_flow_cell_path"
)
@mock.patch("cg.meta.tar.tar.TarAPI")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.store")
def test_fetch_flow_cell_integration(
    mock_store,
    mock_flow_cell,
    mock_tar,
    mock_flow_cell_path,
    mock_key_path,
    mock_query,
    mock_create_copy_complete,
    mock_create_rta_complete,
    mock_unlink_files,
    cg_context,
    dsmc_q_archive_output,
    caplog,
):
    """Component integration test for the BackupAPI, fetching a specified flow cell"""

    caplog.set_level(logging.INFO)

    # GIVEN we want to retrieve a specific flow cell from PDC
    backup_api = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status=mock_store,
        tar_api=mock_tar,
        pdc_service=mock.Mock(),
        flow_cells_dir=cg_context.run_instruments.illumina.sequencing_runs_dir,
    )
    mock_flow_cell.status = FlowCellStatus.REQUESTED
    mock_flow_cell.sequencer_type = Sequencers.NOVASEQ
    mock_store.get_flow_cells_by_statuses.return_value.count.return_value = 0
    mock_query.return_value = dsmc_q_archive_output

    backup_api.tar_api.run_tar_command.return_value = None
    result = backup_api.fetch_flow_cell(flow_cell=mock_flow_cell)

    # THEN the process to retrieve the flow cell from PDC is started
    assert "retrieving from PDC" in caplog.text

    # AND when done the status of that flow cell is set to "retrieved"
    assert (
        f"Status for flow cell {mock_flow_cell.name} set to {FlowCellStatus.RETRIEVED}"
        in caplog.text
    )
    assert mock_flow_cell.status == "retrieved"

    # AND status-db is updated with the new status
    assert mock_store.session.commit.called

    # AND the elapsed time of the retrieval process is returned
    assert result > 0


def test_validate_is_flow_cell_backup_possible(
    base_store: Store,
    caplog,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
):
    """Tests checking if a back-up of flow-cell is possible."""
    caplog.set_level(logging.DEBUG)
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service

    # GIVEN a backup service
    backup_service = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status=base_store,
        tar_api=mock.Mock(),
        pdc_service=pdc_service,
        flow_cells_dir=cg_context.run_instruments.illumina.sequencing_runs_dir,
    )

    # GIVEN no Dsmc process is running

    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=illumina_run_encryption_service.run_dir_data.id,
        store=base_store,
    )

    # GIVEN that encryption is completed
    illumina_run_encryption_service.run_encryption_dir.mkdir(parents=True)
    illumina_run_encryption_service.complete_file_path.touch()

    # WHEN checking if back-up is possible
    backup_service.validate_is_flow_cell_backup_possible(
        db_flow_cell=db_flow_cell, illumina_run_encryption_service=illumina_run_encryption_service
    )

    # THEN communicate that it passed
    assert "Flow cell can be backed up" in caplog.text


def test_validate_is_flow_cell_backup_when_dsmc_is_already_running(
    base_store: Store,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    mocker,
):
    """Tests checking if a back-up of flow-cell is possible when Dsmc is already running."""
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service

    # GIVEN a backup service
    backup_service = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status=base_store,
        tar_api=mock.Mock(),
        pdc_service=pdc_service,
        flow_cells_dir=cg_context.run_instruments.illumina.sequencing_runs_dir,
    )

    # GIVEN a Dsmc process is already running
    mocker.patch.object(PdcService, "validate_is_dsmc_running", return_value=True)

    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=illumina_run_encryption_service.run_dir_data.id,
        store=base_store,
    )

    # WHEN checking if back-up is possible
    with pytest.raises(DsmcAlreadyRunningError):
        backup_service.validate_is_flow_cell_backup_possible(
            db_flow_cell=db_flow_cell,
            illumina_run_encryption_service=illumina_run_encryption_service,
        )

        # THEN error should be raised


def test_validate_is_flow_cell_backup_when_already_backed_up(
    base_store: Store,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
):
    """Tests checking if a back-up of flow-cell is possible when flow cell is already backed up."""
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service

    # GIVEN a backup service
    backup_service = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status=base_store,
        tar_api=mock.Mock(),
        pdc_service=pdc_service,
        flow_cells_dir=cg_context.run_instruments.illumina.sequencing_runs_dir,
    )

    # GIVEN a database flow cell which is backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=illumina_run_encryption_service.run_dir_data.id,
        store=base_store,
        has_backup=True,
    )

    # WHEN checking if back-up is possible
    with pytest.raises(FlowCellAlreadyBackedUpError):
        backup_service.validate_is_flow_cell_backup_possible(
            db_flow_cell=db_flow_cell,
            illumina_run_encryption_service=illumina_run_encryption_service,
        )

        # THEN error should be raised


def test_validate_is_flow_cell_backup_when_encryption_is_not_complete(
    base_store: Store,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
):
    """Tests checking if a back-up of flow-cell is possible when encryption is not complete."""
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service

    # GIVEN a backup service
    backup_service = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status=base_store,
        tar_api=mock.Mock(),
        pdc_service=pdc_service,
        flow_cells_dir=cg_context.run_instruments.illumina.sequencing_runs_dir,
    )

    # GIVEN a database flow cell which is backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=illumina_run_encryption_service.run_dir_data.id,
        store=base_store,
    )

    # WHEN checking if back-up is possible
    with pytest.raises(IlluminaRunEncryptionError):
        backup_service.validate_is_flow_cell_backup_possible(
            db_flow_cell=db_flow_cell,
            illumina_run_encryption_service=illumina_run_encryption_service,
        )

        # THEN error should be raised


def test_backup_flow_cell(
    base_store: Store,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    mocker,
):
    """Tests back-up flow cell."""
    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service

    # GIVEN a backup service
    backup_service = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status=base_store,
        tar_api=mock.Mock(),
        pdc_service=pdc_service,
        flow_cells_dir=cg_context.run_instruments.illumina.sequencing_runs_dir,
    )
    # GIVEN a mocked archiving call
    mocker.patch.object(PdcService, "archive_file_to_pdc", return_value=None)

    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=illumina_run_encryption_service.run_dir_data.id,
        store=base_store,
    )

    # WHEN backing up flow cell
    backup_service.backup_flow_cell(
        files_to_archive=[
            illumina_run_encryption_service.final_passphrase_file_path,
            illumina_run_encryption_service.encrypted_gpg_file_path,
        ],
        store=base_store,
        db_flow_cell=db_flow_cell,
    )

    # THEN flow cell should hava a back-up
    assert db_flow_cell.has_backup


def test_backup_flow_cell_when_unable_to_archive(
    base_store: Store,
    cg_context: CGConfig,
    helpers: StoreHelpers,
    illumina_run_encryption_service: IlluminaRunEncryptionService,
    caplog,
):
    """Tests back-up flow cell when unable to archive."""
    caplog.set_level(logging.DEBUG)

    # GIVEN an instance of the PDC API
    pdc_service = cg_context.pdc_service

    # GIVEN a backup service
    backup_service = IlluminaBackupService(
        encryption_api=mock.Mock(),
        pdc_archiving_directory=cg_context.illumina_backup_service.pdc_archiving_directory,
        status=base_store,
        tar_api=mock.Mock(),
        pdc_service=pdc_service,
        flow_cells_dir=cg_context.run_instruments.illumina.sequencing_runs_dir,
    )
    # GIVEN a database flow cell which is not backed up
    db_flow_cell: Flowcell = helpers.add_flow_cell(
        flow_cell_name=illumina_run_encryption_service.run_dir_data.id,
        store=base_store,
    )

    # GIVEN that archiving fails
    with mock.patch(
        "cg.utils.commands.subprocess.run",
        return_value=create_process_response(return_code=EXIT_FAIL),
    ):
        # WHEN backing up flow cell

        # THEN the appropriate error should have been raised
        with pytest.raises(PdcError):
            backup_service.backup_flow_cell(
                files_to_archive=[
                    illumina_run_encryption_service.final_passphrase_file_path,
                    illumina_run_encryption_service.encrypted_gpg_file_path,
                ],
                store=base_store,
                db_flow_cell=db_flow_cell,
            )
