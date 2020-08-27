"""Test MIP get files and build bundle"""
import mock
import pytest

from snapshottest import Snapshot

import cg.meta.store.mip as store_mip
from cg.exc import (
    AnalysisNotFinishedError,
    BundleAlreadyAddedError,
)


@mock.patch("cg.store.Store")
@mock.patch("cg.apps.hk.HousekeeperAPI")
@mock.patch("cg.meta.store.mip.add_analysis")
def test_gather_files_and_bundle_in_hk_bundle_already_added(
    mock_add_analysis, mock_housekeeper, mock_cg_store, config_stream, bundle_data
):
    """
    tests the function gather_files_and_bundle_in_housekeeper
    """
    # GIVEN a MIP RNA analysis config file
    mip_rna_config = config_stream["rna_config_store"]

    # WHEN the bundle has already been added to Housekeeper
    mock_add_analysis.return_value = bundle_data
    mock_housekeeper.add_bundle.return_value = None

    # THEN the BundleAlreadyAddedError exception should be raised
    with pytest.raises(BundleAlreadyAddedError) as exc_info:
        store_mip.gather_files_and_bundle_in_housekeeper(
            mip_rna_config, mock_housekeeper, mock_cg_store
        )

    assert exc_info.value.message == "bundle already added"


@mock.patch("cg.store.Store")
@mock.patch("housekeeper.store.models")
@mock.patch("cg.apps.hk.HousekeeperAPI")
@mock.patch("cg.meta.store.mip.reset_case_action")
@mock.patch("cg.meta.store.mip.add_new_analysis")
@mock.patch("cg.meta.store.mip.add_analysis")
def test_gather_files_and_bundle_in_hk_bundle_new_analysis(
    mock_add_analysis,
    mock_add_new_analysis,
    mock_reset_case_action,
    mock_housekeeper_api,
    mock_housekeeper_store,
    mock_cg_store,
    config_stream,
    bundle_data,
):
    """
    tests the function gather_files_and_bundle_in_housekeeper
    """
    # GIVEN a MIP RNA analysis config file
    mip_rna_config = config_stream["rna_config_store"]

    # WHEN adding a new bundle to Housekeeper
    mock_add_analysis.return_value = bundle_data
    mock_bundle = mock_housekeeper_store.Bundle.return_value
    mock_version = mock_housekeeper_store.Version.return_value
    mock_housekeeper_api.add_bundle.return_value = (mock_bundle, mock_version)
    mock_case = mock_cg_store.Family.return_value
    mock_reset_case_action(mock_case)
    mock_add_new_analysis.return_value = mock_cg_store.Analysis.return_value

    store_mip.gather_files_and_bundle_in_housekeeper(
        mip_rna_config, mock_housekeeper_api, mock_cg_store
    )

    # THEN the bundle and version should be added to Housekeeper
    mock_housekeeper_api.include.assert_called()
    mock_housekeeper_api.include.assert_called_with(mock_version)
    mock_housekeeper_api.add_commit.assert_called()
    mock_housekeeper_api.add_commit.assert_called_with(mock_bundle, mock_version)


@mock.patch("cg.meta.store.mip.build_bundle")
@mock.patch("cg.meta.store.mip.parse_sampleinfo")
@mock.patch("cg.meta.store.mip.parse_config")
def test_add_analysis_finished(
    mock_parse_config,
    mock_parse_sample,
    mock_build_bundle,
    config_stream,
    config_data_rna,
    sampleinfo_data,
    rna_deliverables_raw,
):
    """
    tests the function add_analysis when passing a config file of a finished RNA analysis
    """
    # GIVEN a MIP RNA analysis configuration file
    mip_rna_config = config_stream["rna_config_store"]

    # WHEN gathering information from the MIP RNA analysis to store and the analysis is
    # finished
    mock_parse_config.return_value = config_data_rna
    mock_parse_sample.return_value = sampleinfo_data

    result = store_mip.add_analysis(mip_rna_config)

    # THEN the function add_analysis should call the function build_bundle with the correct
    # parameters and return a new bundle
    mock_build_bundle.assert_called()
    mock_build_bundle.assert_called_with(config_data_rna, sampleinfo_data, rna_deliverables_raw)
    assert result == mock_build_bundle(config_data_rna, sampleinfo_data, rna_deliverables_raw)


@mock.patch("cg.meta.store.mip.parse_sampleinfo")
@mock.patch("cg.meta.store.mip.parse_config")
def test_add_analysis_not_finished(
    mock_parse_config, mock_parse_sample, config_stream, config_data_rna, sampleinfo_data
):
    """
    tests the function add_analysis when passing a config file of an unfinished RNA analysis
    """
    # GIVEN a MIP RNA analysis configuration file

    mip_rna_config = config_stream["rna_config_store"]
    mock_parse_config.return_value = config_data_rna
    sampleinfo_data["is_finished"] = False
    mock_parse_sample.return_value = sampleinfo_data

    # WHEN  gathering information from the MIP RNA analysis to store and the analysis is not
    # finished

    with pytest.raises(AnalysisNotFinishedError) as exc_info:
        store_mip.add_analysis(mip_rna_config)

    # THEN the correct exception should be raised
    assert exc_info.value.message == "analysis not finished"


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
