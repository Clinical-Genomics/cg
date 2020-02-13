"""Test MIP RNA get files and build bundle"""

from snapshottest import Snapshot

import cg.meta.store.mip_rna as mip_rna


def test_get_rna_files(snapshot: Snapshot, files_data: dict):
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN config data of a "sharp" RNA run (not dry run)
    mip_rna_config = files_data["rna_config"]

    # GIVEN sampleinfo input from a finished RNA analysis
    rna_sampleinfo = files_data["rna_sampleinfo"]

    mip_rna_file_data = mip_rna.get_files_rna(mip_rna_config, rna_sampleinfo)

    # THEN the result should contain the data as specified by the MIP bundle
    snapshot.assert_match(mip_rna_file_data)


def test_build_bundle_rna(snapshot: Snapshot, files_data: dict):
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN config data of a "sharp" RNA run (not dry run)
    mip_rna_config = files_data["rna_config"]

    # GIVEN sampleinfo input from a finished RNA analysis
    rna_sampleinfo = files_data["rna_sampleinfo"]

    mip_rna_bundle = mip_rna.build_bundle_rna(mip_rna_config, rna_sampleinfo)

    # THEN the result should contain the data as specified by the MIP version
    snapshot.assert_match(mip_rna_bundle)


def test_build_bundle_rna_no_missing_vpstderr(snapshot: Snapshot, files_data: dict):
    """
    Args:
    files_raw (dict): With dicts from files
    """
    # GIVEN config data of a "sharp" RNA run (not dry run)
    mip_rna_config = files_data["rna_config"]

    # GIVEN sampleinfo input from a finished RNA analysis and a vp_srderr_file is present
    rna_sampleinfo = files_data["rna_sampleinfo"]
    rna_sampleinfo["vp_stderr_file"] = "/some/path/file.name"

    mip_rna_bundle = mip_rna.build_bundle_rna(mip_rna_config, rna_sampleinfo)

    # THEN the result should contain the data as specified by the MIP bundle
    snapshot.assert_match(mip_rna_bundle)
