"""Test MIP get files and build bundle"""
import mock
import pytest

from snapshottest import Snapshot

import cg.meta.store.mip as store_mip
from cg.exc import (
    AnalysisNotFinishedError,
    BundleAlreadyAddedError,
)


@mock.patch("cg.meta.store.base.build_bundle")
@mock.patch("cg.meta.store.mip.parse_sampleinfo")
@mock.patch("cg.meta.store.mip.parse_config")
def test_add_mip_analysis_finished(
    mock_parse_config,
    mock_parse_sample,
    mock_build_bundle,
    config_stream,
    config_data_rna,
    sampleinfo_data,
    rna_deliverables_raw,
):
    """
    tests the function add_mip_analysis when passing a config file of a finished RNA analysis
    """
    # GIVEN a MIP RNA analysis configuration file
    mip_rna_config = config_stream["rna_config_store"]

    # WHEN gathering information from the MIP RNA analysis to store and the analysis is
    # finished
    mock_parse_config.return_value = config_data_rna
    mock_parse_sample.return_value = sampleinfo_data

    result = store_mip.add_mip_analysis(mip_rna_config)

    # THEN the function add_mip_analysis should call the function build_bundle with the correct
    # parameters and return a new bundle
    mock_build_bundle.assert_called()
    mock_build_bundle.assert_called_with(config_data_rna, sampleinfo_data, rna_deliverables_raw)
    assert result == mock_build_bundle(config_data_rna, sampleinfo_data, rna_deliverables_raw)


def test_parse_config(snapshot: Snapshot, config_raw: dict):
    """
    tests the function parse_config against a snapshot
    """
    # GIVEN the raw MIP analysis config file

    # WHEN getting the files used to build the bundle
    mip_rna_parse_config = store_mip.parse_config(config_raw)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_parse_config)


def test_parse_sampleinfo_data(snapshot: Snapshot, files_raw):
    """
    tests the function parse_sampleinfo_data against a snapshot
    """
    # GIVEN the raw MIP sample info file

    rna_sampleinfo = files_raw["rna_sampleinfo"]

    # WHEN getting the smaple info used to build the bundle
    mip_rna_parse_sampleinfo = store_mip.parse_sampleinfo(rna_sampleinfo)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_parse_sampleinfo)
