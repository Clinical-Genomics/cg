"""Tests for cleaning flow cell run directories using
cg.meta.clean.flow_cell_run_directories.RunDirFlowCell."""
from unittest import mock

from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.meta.clean.flow_cell_run_directories import RunDirFlowCell


@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_age(
    mock_statusdb,
    mock_hk,
    flow_cell_path,
    timestamp_yesterday,
):
    # GIVEN a flow cell with a sequenced date:
    flow_cell: RunDirFlowCell = RunDirFlowCell(flow_cell_path, mock_statusdb, mock_hk)
    flow_cell._sequenced_date = timestamp_yesterday

    # WHEN determining the age of a flow cell
    result = flow_cell.age

    # THEN the age property of the flow cell should be set to 1 day
    assert result == 1


@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_sequenced_date_from_statusdb(
    mock_statusdb,
    mock_hk,
    flow_cell_path,
    timestamp_yesterday,
):
    # GIVEN a flow cell with a sequenced_at date in statusdb
    flow_cell: RunDirFlowCell = RunDirFlowCell(flow_cell_path, mock_statusdb, mock_hk)
    mock_statusdb.get_flow_cell.return_value.sequenced_at = timestamp_yesterday

    # WHEN determining the age of a flow cell
    result = flow_cell.sequenced_date

    # THEN the sequenced_date property of the flow cell should be set to the sequenced_at date in
    # statusdb
    assert result == timestamp_yesterday


@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_sequenced_date_from_run_name(
    mock_statusdb,
    mock_hk,
    flow_cell_path,
):
    # GIVEN a flow cell that does not exist in statusdb
    flow_cell: RunDirFlowCell = RunDirFlowCell(flow_cell_path, mock_statusdb, mock_hk)
    mock_statusdb.get_flow_cell.return_value = None

    # WHEN determining the age of a flow cell
    result = flow_cell.sequenced_date

    # THEN the sequenced_date property of the flow cell should be derived from the run name of
    # the flow cell
    assert result == flow_cell.derived_date


@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.store.Store")
def test_archive_sample_sheet_no_bundle(mock_statusdb, mock_hk, flow_cell_path, novaseq_dir):
    # GIVEN a flow cell
    flow_cell: RunDirFlowCell = RunDirFlowCell(flow_cell_path, mock_statusdb, mock_hk)
    # GIVEN a sample sheet connected to the flow cell
    flow_cell.sample_sheet_path = novaseq_dir / DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME
    # GIVEN there is no bundle for the flow cell
    mock_hk.bundle.return_value = None
    # GIVEN the sample sheet does not exist in Housekeeper
    mock_hk.files.return_value.first.return_value = None
    mock_hk.get_files.return_value.first.return_value.is_included = False

    # WHEN archiving the sample sheet
    flow_cell.archive_sample_sheet()

    # THEN a bundle and version should be created for the flow cell
    flow_cell.hk.create_new_bundle_and_version.assert_called_once_with(name=flow_cell.id)

    # THEN the sample sheet should be be added to Housekeeper
    flow_cell.hk.add_and_include_file_to_latest_version.assert_called_once_with(
        bundle_name=flow_cell.id,
        file=flow_cell.sample_sheet_path,
        tags=[SequencingFileTag.ARCHIVED_SAMPLE_SHEET, flow_cell.id],
    )
