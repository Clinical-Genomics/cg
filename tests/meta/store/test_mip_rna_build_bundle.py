# -*- coding: utf-8 -*-
"""Test MIP RNA get files and build bundle"""
from snapshottest import Snapshot
import mock
import pytest

import cg.meta.store.mip_rna as mip_rna

from cg.exc import AnalysisNotFinishedError, BundleAlreadyAddedError


@mock.patch("cg.store.Store")
@mock.patch("cg.apps.hk.HousekeeperAPI")
@mock.patch("cg.meta.store.mip_rna.add_analysis")
def test_gather_files_and_bundle_in_hk_bundle_already_added(
    mock_add_analysis, mock_housekeeper, mock_store, config_stream, bundle_data
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
        mip_rna.gather_files_and_bundle_in_housekeeper(
            mip_rna_config, mock_housekeeper, mock_store
        )

    assert exc_info.value.message == "bundle already added"


@mock.patch("cg.store.Store")
@mock.patch("housekeeper.store.models")
@mock.patch("cg.apps.hk.HousekeeperAPI")
@mock.patch("cg.meta.store.mip_rna.include_files_in_housekeeper")
@mock.patch("cg.meta.store.mip_rna.add_new_complete_analysis_record")
@mock.patch("cg.meta.store.mip_rna.add_new_analysis_to_the_status_api")
@mock.patch("cg.meta.store.mip_rna.add_analysis")
def test_gather_files_and_bundle_in_hk_bundle_new_analysis(
    mock_add_analysis,
    mock_add_to_status,
    mock_add_new_analysis,
    mock_include_files_in_housekeeper,
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
    mock_add_to_status.return_value = mock_cg_store.Family.return_value
    mock_add_new_analysis.return_value = mock_cg_store.Analysis.return_value

    mip_rna.gather_files_and_bundle_in_housekeeper(
        mip_rna_config, mock_housekeeper_api, mock_cg_store
    )

    # THEN the bundle and version should be added to Housekeeper
    mock_include_files_in_housekeeper.assert_called()
    mock_include_files_in_housekeeper.assert_called_with(
        mock_bundle, mock_housekeeper_api, mock_version
    )


@mock.patch("cg.meta.store.mip_rna.build_bundle")
@mock.patch("cg.meta.store.mip_rna.parse_sampleinfo")
@mock.patch("cg.meta.store.mip_rna.parse_config")
def test_add_analysis_finished(
    mock_parse_config,
    mock_parse_sample,
    mock_build_bundle,
    config_stream,
    config_data,
    sampleinfo_data,
    deliverables_raw,
):
    """
    tests the function add_analysis when passing a config file of a finished RNA analysis
    """
    # GIVEN a MIP RNA analysis configuration file
    mip_rna_config = config_stream["rna_config_store"]

    # WHEN gathering information from the MIP RNA analysis to store and the analysis is
    # finished
    mock_parse_config.return_value = config_data
    mock_parse_sample.return_value = sampleinfo_data

    result = mip_rna.add_analysis(mip_rna_config)

    # THEN the function add_analysis should call the function build_bundle with the correct
    # parameters and return a new bundle
    mock_build_bundle.assert_called()
    mock_build_bundle.assert_called_with(config_data, sampleinfo_data, deliverables_raw)
    assert result == mock_build_bundle(config_data, sampleinfo_data, deliverables_raw)


@mock.patch("cg.meta.store.mip_rna.parse_sampleinfo")
@mock.patch("cg.meta.store.mip_rna.parse_config")
def test_add_analysis_not_finished(
    mock_parse_config, mock_parse_sample, config_stream, config_data, sampleinfo_data
):
    """
    tests the function add_analysis when passing a config file of an unfinished RNA analysis
    """
    # GIVEN a MIP RNA analysis configuration file

    mip_rna_config = config_stream["rna_config_store"]
    mock_parse_config.return_value = config_data
    sampleinfo_data["is_finished"] = False
    mock_parse_sample.return_value = sampleinfo_data

    # WHEN  gathering information from the MIP RNA analysis to store and the analysis is not
    # finished

    with pytest.raises(AnalysisNotFinishedError) as exc_info:
        mip_rna.add_analysis(mip_rna_config)

    # THEN the correct exception should be raised
    assert exc_info.value.message == "analysis not finished"


def test_build_bundle(
    snapshot: Snapshot, config_data: dict, sampleinfo_data: dict, deliverables_raw: dict
):
    # GIVEN the MIP analysis config data, the sampleinfo data and the deliverables file

    # WHEN building the bundle
    mip_rna_bundle = mip_rna.build_bundle(
        config_data, sampleinfo_data, deliverables_raw
    )

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_bundle)


def test_get_files(snapshot: Snapshot, deliverables_raw: dict):
    # GIVEN the MIP analysis deliverables file

    # WHEN getting the files used to build the bundle
    mip_rna_files = mip_rna.get_files(deliverables_raw)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_files)


def test_parse_config(snapshot: Snapshot, config_raw: dict):
    # GIVEN the raw MIP analysis config file

    # WHEN getting the files used to build the bundle
    mip_rna_parse_config = mip_rna.parse_config(config_raw)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_parse_config)
