""" tests for the meta BackupAPI """

import logging
import subprocess

import mock
import pytest
from cg.meta.backup import BackupApi


@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_maximum_flowcells_ondisk_reached(mock_store, mock_pdc):
    """tests maximum_flowcells_ondisk method of the backup api"""
    # GIVEN a flowcell needs to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN the number of flowcells with status "ondisk" greater than the maximum number allowed
    mock_store.flowcells(status="ondisk").count.return_value = 2000

    # THEN this method should return True
    assert backup_api.maximum_flowcells_ondisk() is True


@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_maximum_flowcells_ondisk_not_reached(mock_store, mock_pdc):
    """tests maximum_flowcells_ondisk method of the backup api"""
    # GIVEN a flowcell needs to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN the number of flowcells with status "ondisk" less than the maximum number allowed
    mock_store.flowcells(status="ondisk").count.return_value = 1000

    # THEN this method should return False
    assert backup_api.maximum_flowcells_ondisk() is False


@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_maximum_processing_queue_full(mock_store, mock_pdc):
    """tests check_processing method of the backup api"""
    # GIVEN a flowcell needs to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN there's already a flowcell being retrieved from PDC
    mock_store.flowcells(status="processing").count.return_value = 1

    # THEN this method should return False
    assert backup_api.check_processing(max_processing_flowcells=1) is False


@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_maximum_processing_queue_not_full(mock_store, mock_pdc):
    """tests check_processing method of the backup api"""
    # GIVEN a flowcell needs to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN there are no flowcells being retrieved from PDC
    mock_store.flowcells(status="processing").count.return_value = 0

    # THEN this method should return True
    assert backup_api.check_processing(max_processing_flowcells=1) is True


@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_pop_flowcell_next_requested(mock_store, mock_pdc, mock_flowcell):
    """tests pop_flowcell method of the backup api"""
    # GIVEN status-db needs to be checked for flowcells to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN a flowcell is requested to be retrieved from PDC
    mock_store.flowcells(status="requested").first.return_value = mock_flowcell

    popped_flowcell = backup_api.pop_flowcell(dry_run=False)

    # THEN a flowcell is returned, the status is set to "processing", and status-db is updated with
    # the new status
    assert popped_flowcell is not None


@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_pop_flowcell_dry_run(mock_store, mock_pdc, mock_flowcell):
    """tests pop_flowcell method of the backup api"""
    # GIVEN status-db needs to be checked for flowcells to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN a flowcell is requested to be retrieved from PDC
    # AND it's a  dry run
    popped_flowcell = backup_api.pop_flowcell(dry_run=True)

    # THEN a flowcell is returned, the status is set to "processing", but status-db is NOT updated with
    # the new status
    assert popped_flowcell is not None
    assert not mock_store.commit.called


@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_pop_flowcell_no_flowcell_requested(mock_store, mock_pdc):
    """tests pop_flowcell method of the backup api"""
    # GIVEN status-db needs to be checked for flowcells to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN there are no flowcells requested to be retrieved from PDC
    mock_store.flowcells(status="requested").first.return_value = None

    popped_flowcell = backup_api.pop_flowcell(dry_run=False)

    # THEN no flowcell is returned
    assert popped_flowcell is None


@mock.patch("cg.meta.backup.BackupApi.check_processing")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_fetch_flowcell_processing_queue_full(
    mock_store, mock_pdc, mock_flowcell, mock_check_processing, caplog
):
    """tests the fetch_flowcell method of the backup API"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flowcell needs to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN the processing queue is full
    backup_api.check_processing.return_value = False
    result = backup_api.fetch_flowcell(mock_flowcell, dry_run=False)

    # THEN no flowcell will be fetched and a log message indicates that the processing queue is
    # full
    assert result is None
    assert "processing queue is full" in caplog.text


@mock.patch("cg.meta.backup.BackupApi.maximum_flowcells_ondisk")
@mock.patch("cg.meta.backup.BackupApi.check_processing")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_fetch_flowcell_max_flowcells_ondisk(
    mock_store,
    mock_pdc,
    mock_flowcell,
    mock_check_processing,
    mock_maximum_flowcells_ondisk,
    caplog,
):
    """tests the fetch_flowcell method of the backup API"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flowcell needs to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN the processing queue is not full but the number of flowcells on disk is greater than the
    # maximum
    backup_api.check_processing.return_value = True
    backup_api.maximum_flowcells_ondisk.return_value = True

    result = backup_api.fetch_flowcell(mock_flowcell, dry_run=False)

    # THEN no flowcell will be fetched and a log message indicates that maximum number of flowcells
    # has been reached
    assert result is None
    assert "maximum flowcells ondisk reached" in caplog.text


@mock.patch("cg.meta.backup.BackupApi.pop_flowcell")
@mock.patch("cg.meta.backup.BackupApi.maximum_flowcells_ondisk")
@mock.patch("cg.meta.backup.BackupApi.check_processing")
@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_fetch_flowcell_no_flowcells_requested(
    mock_store,
    mock_pdc,
    mock_check_processing,
    mock_maximum_flowcells_ondisk,
    mock_pop_flowcell,
    caplog,
):
    """tests the fetch_flowcell method of the backup API"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flowcell needs to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN no flowcells are requested
    mock_pop_flowcell.return_value = None
    backup_api.check_processing.return_value = True
    backup_api.maximum_flowcells_ondisk.return_value = False

    # AND no flowcell has been specified
    mock_flowcell = None

    result = backup_api.fetch_flowcell(mock_flowcell, dry_run=False)

    # THEN no flowcell will be fetched and a log message indicates that no flowcells have been
    # requested
    assert result is None
    assert "no flowcells requested" in caplog.text


@mock.patch("cg.meta.backup.BackupApi.pop_flowcell")
@mock.patch("cg.meta.backup.BackupApi.maximum_flowcells_ondisk")
@mock.patch("cg.meta.backup.BackupApi.check_processing")
@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_fetch_flowcell_retrieve_next_flowcell(
    mock_store,
    mock_pdc,
    mock_check_processing,
    mock_maximum_flowcells_ondisk,
    mock_pop_flowcell,
    caplog,
):
    """tests the fetch_flowcell method of the backup API"""

    caplog.set_level(logging.INFO)

    # GIVEN we check if a flowcell needs to be retrieved from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )

    # WHEN no flowcells is specified, but a flowcell in status-db has the status "requested"
    mock_flowcell = None
    mock_pop_flowcell.return_value = mock_store.add_flowcell(
        status="requested",
    )
    backup_api.check_processing.return_value = True
    backup_api.maximum_flowcells_ondisk.return_value = False

    result = backup_api.fetch_flowcell(mock_flowcell, dry_run=False)

    # THEN the process to retrieve the flowcell from PDC is started
    assert "retrieving from PDC" in caplog.text

    # AND when done the status of that flowcell is set to "retrieved"
    assert (
        f'Status for flowcell {mock_pop_flowcell.return_value.name} set to "retrieved"'
        in caplog.text
    )
    assert mock_pop_flowcell.return_value.status == "retrieved"

    # AND status-db is updated with the new status
    assert mock_store.commit.called

    # AND the elapsed time of the retrieval process is returned
    assert result > 0


@mock.patch("cg.meta.backup.BackupApi.maximum_flowcells_ondisk")
@mock.patch("cg.meta.backup.BackupApi.check_processing")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_fetch_flowcell_retrieve_specified_flowcell(
    mock_store,
    mock_pdc,
    mock_flowcell,
    mock_check_processing,
    mock_maximum_flowcells_ondisk,
    caplog,
):
    """tests the fetch_flowcell method of the backup API"""

    caplog.set_level(logging.INFO)

    # GIVEN we want to retrieve a specific flowcell from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )
    backup_api.check_processing.return_value = True
    backup_api.maximum_flowcells_ondisk.return_value = False

    result = backup_api.fetch_flowcell(mock_flowcell, dry_run=False)

    # THEN the process to retrieve the flowcell from PDC is started
    assert "retrieving from PDC" in caplog.text

    # AND when done the status of that flowcell is set to "retrieved"
    assert f'Status for flowcell {mock_flowcell.name} set to "retrieved"' in caplog.text
    assert mock_flowcell.status == "retrieved"

    # AND status-db is updated with the new status
    assert mock_store.commit.called

    # AND the elapsed time of the retrieval process is returned
    assert result > 0


@mock.patch("cg.meta.backup.BackupApi.maximum_flowcells_ondisk")
@mock.patch("cg.meta.backup.BackupApi.check_processing")
@mock.patch("cg.store.models.Flowcell")
@mock.patch("cg.apps.pdc")
@mock.patch("cg.store")
def test_fetch_flowcell_pdc_retrieval_failed(
    mock_store,
    mock_pdc,
    mock_flowcell,
    mock_check_processing,
    mock_maximum_flowcells_ondisk,
    caplog,
):
    """tests the fetch_flowcell method of the backup API"""

    caplog.set_level(logging.INFO)

    # GIVEN we are going to retrieve a flowcell from PDC
    backup_api = BackupApi(
        mock_store, mock_pdc, max_flowcells_on_disk=1250, root_dir="/path/to/root_dir"
    )
    backup_api.check_processing.return_value = True
    backup_api.maximum_flowcells_ondisk.return_value = False

    # WHEN the retrieval process fails
    mock_pdc.retrieve_flowcell.side_effect = subprocess.CalledProcessError(1, "echo")
    with pytest.raises(subprocess.CalledProcessError):
        backup_api.fetch_flowcell(mock_flowcell, dry_run=False)

    # THEN the failure to retrieve is logged
    assert "retrieval failed" in caplog.text
