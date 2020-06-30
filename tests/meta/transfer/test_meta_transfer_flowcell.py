"""Tests for transfer flowcell data"""
import datetime as dt
import warnings

from sqlalchemy import exc as sa_exc


def test_transfer_flowcell(flowcell_store, transfer_flowcell_api):

    # GIVEN a store with a received but not sequenced sample
    flowcell_id = "HJKMYBCXX"
    housekeeper_api = transfer_flowcell_api.hk
    assert flowcell_store.samples().count() == 1
    assert flowcell_store.flowcells().count() == 0
    assert housekeeper_api.bundles().count() == 0

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

    # ... and it should store the fastq files for the sample in housekeeper
    hk_bundle = housekeeper_api.bundle(status_sample.internal_id)

    assert len(hk_bundle.versions[0].files) > 0

    for hk_file in hk_bundle.versions[0].files:
        assert hk_file.path.endswith("fastq.gz")
