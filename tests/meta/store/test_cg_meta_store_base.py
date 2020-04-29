"""Test store base module: MIP get files and build bundle"""
from snapshottest import Snapshot

import cg.meta.store.base as store_base


def test_build_bundle(
    snapshot: Snapshot, config_data: dict, sampleinfo_data: dict, deliverables_raw: dict
):
    """
        tests the function_build bundle against a snapshot
    """
    # GIVEN the MIP analysis config data, the sampleinfo data and the deliverables file

    # WHEN building the bundle
    mip_rna_bundle = store_base.build_bundle(config_data, sampleinfo_data, deliverables_raw)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_bundle)


def test_get_files(snapshot: Snapshot, deliverables_raw: dict):
    """
        tests the function get_files against a snapshot
    """
    # GIVEN the MIP RNA analysis deliverables file
    pipeline = "wts"

    # WHEN getting the files used to build the bundle
    mip_rna_files = store_base.get_files(deliverables_raw, pipeline)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_files)
