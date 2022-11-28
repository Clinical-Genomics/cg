"""Tests for transfer flow cell data."""
from datetime import datetime
import warnings
from pathlib import Path
from typing import Generator

from sqlalchemy import exc as sa_exc

from cg.constants import FlowCellStatus
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.meta.transfer import TransferFlowCell
from cg.store import Store


def test_transfer_flow_cell(
    flowcell_store: Store,
    mocker,
    transfer_flow_cell_api: Generator[TransferFlowCell, None, None],
    yet_another_flow_cell_id: str,
):

    # GIVEN a store with a received but not sequenced sample
    flowcell_id = yet_another_flow_cell_id
    housekeeper_api = transfer_flow_cell_api.hk
    assert flowcell_store.samples().count() == 2
    assert flowcell_store.flowcells().count() == 0
    assert housekeeper_api.bundles().count() == 0

    # AND a sample sheet
    mock_sample_sheet = Path("path", "to", DemultiplexingDirsAndFiles.SAMPLE_SHEET_FILE_NAME)
    Path("path", "to").mkdir(parents=True, exist_ok=True)
    mock_sample_sheet.touch()
    mocker.patch.object(TransferFlowCell, "_sample_sheet_path")
    TransferFlowCell._sample_sheet_path.return_value = mock_sample_sheet

    # mock_sample_sheet_path.return_value = "/path/to/samplesheet.csv"
    # mock_path_exists.return_vale = True

    # WHEN transferring the flowcell containing the sample
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        flow_cell = transfer_flow_cell_api.transfer(flow_cell_id=flowcell_id)

    # THEN it should create a new flowcell record
    assert flowcell_store.flowcells().count() == 1
    assert flow_cell.status == FlowCellStatus.ONDISK
    assert isinstance(flow_cell.id, int)
    assert flow_cell.name == flowcell_id
    status_sample = flowcell_store.samples().first()
    assert isinstance(status_sample.sequenced_at, datetime)

    # ... and it should store the fastq files and samplesheet for the sample in housekeeper
    hk_bundle = housekeeper_api.bundle(status_sample.internal_id)

    assert len(hk_bundle.versions[0].files) > 0
    assert (
        len([hk_file for hk_file in hk_bundle.versions[0].files if hk_file.path.endswith("csv")])
        == 1
    )

    for hk_file in hk_bundle.versions[0].files:
        assert hk_file.path.endswith("fastq.gz") or hk_file.path.endswith("csv")
