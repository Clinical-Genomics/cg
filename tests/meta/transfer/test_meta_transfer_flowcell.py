"""Tests for transfer flow cell data."""
from datetime import datetime
import warnings
from pathlib import Path

import mock
from sqlalchemy import exc as sa_exc

from cg.store import Store


@mock.patch("pathlib.Path.exists")
@mock.patch("cg.meta.transfer.flowcell.TransferFlowCell._sample_sheet_path")
def test_transfer_flow_cell(
    mock_sample_sheet_path, mock_path_exists, flowcell_store: Store, transfer_flow_cell_api
):

    # GIVEN a store with a received but not sequenced sample
    flowcell_id = "HJKMYBCXX"
    housekeeper_api = transfer_flow_cell_api.hk
    assert flowcell_store.samples().count() == 2
    assert flowcell_store.flowcells().count() == 0
    assert housekeeper_api.bundles().count() == 0

    # AND a samplesheet
    mock_sample_sheet_path.return_value = "/path/to/samplesheet.csv"
    mock_path_exists.return_vale = True

    # WHEN transferring the flowcell containing the sample
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        flow_cell = transfer_flow_cell_api.transfer(flow_cell_id=flowcell_id)

    # THEN it should create a new flowcell record
    assert flowcell_store.flowcells().count() == 1
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
