"""Test store base module: MIP get files and build bundle"""
import mock
import pytest

from snapshottest import Snapshot

from cg.constants import MIP_RNA_TAGS
import cg.meta.store.base as store_base

from cg.exc import (
    AnalysisDuplicationError,
    PipelineUnknownError,
)


@mock.patch("cg.store.Store")
@mock.patch("housekeeper.store.models")
def test_add_new_analysis_pipeline_exception(mock_housekeeper_store, mock_status):
    """
        test catching the exception when no pipeline is found when creating and adding a new
        analysis to status-db
    """
    # GIVEN a case for which the bundle and version is added to Housekeeper, but there is no
    # pipeline specified on sample level
    mock_bundle = mock_housekeeper_store.Bundle.return_value
    mock_version = mock_housekeeper_store.Version.return_value
    mock_case = mock_status.Family.return_value
    mock_case.links[0].sample.data_analysis = None

    # WHEN creating and adding an analysis object for that case to status-db
    with pytest.raises(PipelineUnknownError) as exc_info:
        store_base.add_new_analysis(mock_bundle, mock_case, mock_status, mock_version)

    # THEN a PipelineUnknownError exception should be raised
    assert exc_info.value.message == f"No pipeline specified in {mock_case}"


@mock.patch("cg.store.Store")
@mock.patch("housekeeper.store.models")
def test_add_new_analysis_duplicate_analysis_exception(mock_housekeeper_store, mock_status):
    """
        test catching the exception when no pipeline is found
    """
    # GIVEN a case for which the bundle and version is added to Housekeeper, but the case already
    # has an analysis object stored in status-db
    mock_bundle = mock_housekeeper_store.Bundle.return_value
    mock_version = mock_housekeeper_store.Version.return_value
    mock_case = mock_status.Family.return_value
    mock_status.analysis = mock_status.analysis.return_value

    # WHEN creating and adding an analysis object for that case to status-db
    with pytest.raises(AnalysisDuplicationError) as exc_info:
        store_base.add_new_analysis(mock_bundle, mock_case, mock_status, mock_version)

    # THEN an AnalysisDuplicationEror should be raised
    assert (
        exc_info.value.message
        == f"Analysis object already exists for {mock_case.internal_id} {mock_version.created_at}"
    )


@mock.patch("cg.store.Store")
@mock.patch("housekeeper.store.models")
def test_add_new_analysis(mock_housekeeper_store, mock_status):
    """
        test adding a new analyis to cg store
    """
    # GIVEN a case for which the bundle and version is added to Housekeeper
    mock_bundle = mock_housekeeper_store.Bundle.return_value
    mock_version = mock_housekeeper_store.Version.return_value
    mock_case = mock_status.Family.return_value
    mock_status.analysis.return_value = None

    # WHEN creating and adding an analysis object for that case in status-db
    new_analysis = store_base.add_new_analysis(mock_bundle, mock_case, mock_status, mock_version)

    # THEN and analysis object for that case should created and returned
    assert new_analysis.family == mock_case


@mock.patch("cg.meta.store.base.deliverables_files")
@mock.patch("cg.meta.store.base._determine_missing_files")
def test_build_bundle(
    mock_missing,
    mock_deliverables_files,
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
    mock_deliverables_files.return_value = {"path": "mock_path"}
    mip_rna_bundle = store_base.build_bundle(config_data, sampleinfo_data, deliverables_raw)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_bundle)


@mock.patch("cg.meta.store.base._determine_missing_files")
def test_parse_files(mock_missing, snapshot: Snapshot, deliverables_raw: dict):
    """
        tests the function parse_files against a snapshot
    """
    # GIVEN the a MIP analysis deliverables file
    mock_missing.return_value = False, []
    pipeline = "wts"
    analysis_type_tags = MIP_RNA_TAGS

    # WHEN getting the files used to build the bundle
    mip_files = store_base.parse_files(deliverables_raw, pipeline, analysis_type_tags)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_files)
