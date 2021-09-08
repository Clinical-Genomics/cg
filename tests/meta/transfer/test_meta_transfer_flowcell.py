"""Tests for transfer flowcell data"""
import datetime as dt
import warnings
from pathlib import Path

import mock
from sqlalchemy import exc as sa_exc

from cg.store import Store


@mock.patch("pathlib.Path.exists")
@mock.patch("cg.meta.transfer.flowcell.TransferFlowcell._sample_sheet_path")
def test_transfer_flowcell(
    mock_sample_sheet_path, mock_path_exists, flowcell_store: Store, transfer_flowcell_api
):

    # GIVEN a store with a received but not sequenced sample
    flowcell_id = "HJKMYBCXX"
    housekeeper_api = transfer_flowcell_api.hk
    assert flowcell_store.samples().count() == 1
    assert flowcell_store.flowcells().count() == 0
    assert housekeeper_api.bundles().count() == 0

    # AND a samplesheet
    mock_sample_sheet_path.return_value = "/path/to/samplesheet.csv"
    mock_path_exists.return_vale = True

    # WHEN transferring the flowcell containing the sample
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)
        flowcell_obj = transfer_flowcell_api.transfer(flowcell_id)

    # THEN it should create a new flowcell record
    assert flowcell_store.flowcells().count() == 1
    assert isinstance(flowcell_obj.id, int)
    assert flowcell_obj.name == flowcell_id
    status_sample = flowcell_store.samples().first()
    assert isinstance(status_sample.sequenced_at, dt.datetime)

    # ... and it should store the fastq files and samplesheet for the sample in housekeeper
    hk_bundle = housekeeper_api.bundle(status_sample.internal_id)

    assert len(hk_bundle.versions[0].files) > 0
    assert (
        len([hk_file for hk_file in hk_bundle.versions[0].files if hk_file.path.endswith("csv")])
        == 1
    )

    for hk_file in hk_bundle.versions[0].files:
        assert hk_file.path.endswith("fastq.gz") or hk_file.path.endswith("csv")
