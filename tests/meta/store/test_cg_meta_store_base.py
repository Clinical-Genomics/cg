"""Test store base module: MIP get files and build bundle"""
import mock
from snapshottest import Snapshot

import cg.meta.store.base as store_base


@mock.patch("cg.meta.store.base._determine_missing_files")
def test_build_bundle(
    mock_missing,
    snapshot: Snapshot,
    config_data: dict,
    sampleinfo_data: dict,
    deliverables_raw: dict,
):
    """
        tests the function_build bundle against a snapshot
    """
    # GIVEN the MIP analysis config data, the sampleinfo data and the deliverables file

    # WHEN building the bundle
    mock_missing.return_value = False, []
    mip_rna_bundle = store_base.build_bundle(config_data, sampleinfo_data, deliverables_raw)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_bundle)


@mock.patch("cg.meta.store.base._determine_missing_files")
def test_get_files(mock_missing, snapshot: Snapshot, deliverables_raw: dict):
    """
        tests the function get_files against a snapshot
    """
    # GIVEN the MIP RNA analysis deliverables file
    mock_missing.return_value = False, []
    pipeline = "wts"

    # WHEN getting the files used to build the bundle
    mip_rna_files = store_base.get_files(deliverables_raw, pipeline)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_files)
