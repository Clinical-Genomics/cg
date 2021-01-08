"""Test store base module: MIP get files and build bundle"""
import mock
import pytest
from snapshottest import Snapshot

import cg.meta.store.base as store_base
from cg.constants import MIP_DNA_TAGS, MIP_RNA_TAGS, Pipeline
from cg.exc import AnalysisDuplicationError, BundleAlreadyAddedError, PipelineUnknownError
from cg.meta.store.base import get_tags


@mock.patch("cg.store.Store")
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.meta.store.mip.add_mip_analysis")
def test_gather_files_and_bundle_in_hk_bundle_already_added(
    mock_add_mip_analysis, mock_housekeeper, mock_cg_store, config_stream, bundle_data
):
    """
    tests the function gather_files_and_bundle_in_housekeeper
    """
    # GIVEN a MIP RNA analysis config file
    mip_rna_config = config_stream["rna_config_store"]

    # WHEN the bundle has already been added to Housekeeper
    mock_add_mip_analysis.return_value = bundle_data
    mock_housekeeper.add_bundle.return_value = None

    # THEN the BundleAlreadyAddedError exception should be raised
    with pytest.raises(BundleAlreadyAddedError) as exc_info:
        store_base.gather_files_and_bundle_in_housekeeper(
            mip_rna_config, mock_housekeeper, mock_cg_store, workflow=Pipeline.MIP_DNA
        )

    assert exc_info.value.message == "bundle already added"


@mock.patch("cg.store.Store")
@mock.patch("housekeeper.store.models")
@mock.patch("cg.apps.housekeeper.hk.HousekeeperAPI")
@mock.patch("cg.meta.store.base.reset_case_action")
@mock.patch("cg.meta.store.base.add_new_analysis")
@mock.patch("cg.meta.store.mip.add_mip_analysis")
def test_gather_files_and_bundle_in_hk_bundle_new_analysis(
    mock_add_mip_analysis,
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
    mock_add_mip_analysis.return_value = bundle_data
    mock_bundle = mock_housekeeper_store.Bundle.return_value
    mock_version = mock_housekeeper_store.Version.return_value
    mock_housekeeper_api.add_bundle.return_value = (mock_bundle, mock_version)
    mock_case = mock_cg_store.Family.return_value
    mock_reset_case_action(mock_case)
    mock_add_new_analysis.return_value = mock_cg_store.Analysis.return_value

    store_base.gather_files_and_bundle_in_housekeeper(
        mip_rna_config, mock_housekeeper_api, mock_cg_store, workflow=Pipeline.MIP_DNA
    )

    # THEN the bundle and version should be added to Housekeeper
    mock_housekeeper_api.include.assert_called()
    mock_housekeeper_api.include.assert_called_with(mock_version)
    mock_housekeeper_api.add_commit.assert_called()
    mock_housekeeper_api.add_commit.assert_called_with(mock_bundle, mock_version)


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
    mock_case.data_analysis = None

    # WHEN creating and adding an analysis object for that case to status-db
    with pytest.raises(PipelineUnknownError) as exc_info:
        store_base.add_new_analysis(
            mock_bundle,
            mock_case,
            mock_status,
            mock_version,
        )

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
    mock_case.data_analysis = Pipeline.MIP_DNA
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
    test adding a new analysis to cg store
    """
    # GIVEN a case for which the bundle and version is added to Housekeeper
    mock_bundle = mock_housekeeper_store.Bundle.return_value
    mock_version = mock_housekeeper_store.Version.return_value
    mock_case = mock_status.Family.return_value
    mock_status.analysis.return_value = None
    mock_case.data_analysis = Pipeline.MIP_DNA

    # WHEN creating and adding an analysis object for that case in status-db
    new_analysis = store_base.add_new_analysis(
        mock_bundle,
        mock_case,
        mock_status,
        mock_version,
    )

    # THEN an analysis object for that case should created and returned
    assert new_analysis.family == mock_case


@mock.patch("cg.meta.store.base.deliverables_files")
@mock.patch("cg.meta.store.base._determine_missing_tags")
def test_build_rna_bundle(
    mock_missing,
    mock_deliverables_files,
    snapshot: Snapshot,
    config_data_rna: dict,
    sampleinfo_data: dict,
    rna_deliverables_raw: dict,
):
    """
    tests the function_build bundle against a snapshot
    """
    # GIVEN the MIP RNA analysis config data, the sampleinfo data and the deliverables file

    # WHEN building the bundle
    mock_missing.return_value = False, []
    mock_deliverables_files.return_value = {"path": "mock_path"}
    mip_rna_bundle = store_base.build_bundle(config_data_rna, sampleinfo_data, rna_deliverables_raw)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_bundle)


@mock.patch("cg.meta.store.base.deliverables_files")
@mock.patch("cg.meta.store.base._determine_missing_tags")
def test_build_dna_bundle(
    mock_missing,
    mock_deliverables_files,
    snapshot: Snapshot,
    config_data_dna: dict,
    sampleinfo_data: dict,
    dna_deliverables_raw: dict,
):
    """
    tests the function_build bundle against a snapshot
    """
    # GIVEN the MIP DNA analysis config data, the sampleinfo data and the deliverables file

    # WHEN building the bundle
    mock_missing.return_value = False, []
    mock_deliverables_files.return_value = {"path": "mock_path"}
    mip_dna_bundle = store_base.build_bundle(config_data_dna, sampleinfo_data, dna_deliverables_raw)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_dna_bundle)


@mock.patch("cg.meta.store.base._determine_missing_tags")
def test_parse_files_rna(mock_missing, snapshot: Snapshot, rna_deliverables_raw: dict):
    """
    tests the function parse_files against a snapshot
    """
    # GIVEN the a MIP RNA analysis deliverables file
    mock_missing.return_value = False, []
    pipeline_tag = ["mip-rna"]
    analysis_type_tags = MIP_RNA_TAGS

    # WHEN getting the files used to build the bundle
    mip_rna_files = store_base.parse_files(rna_deliverables_raw, pipeline_tag, analysis_type_tags)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_rna_files)


@mock.patch("cg.meta.store.base._determine_missing_tags")
def test_parse_files_dna(mock_missing, snapshot: Snapshot, dna_deliverables_raw: dict):
    """
    tests the function parse_files against a snapshot
    """
    # GIVEN the a MIP DNA analysis deliverables file
    mock_missing.return_value = False, []
    pipeline_tags = ["mip-dna"]
    analysis_type_tags = MIP_DNA_TAGS

    # WHEN getting the files used to build the bundle
    mip_dna_files = store_base.parse_files(dna_deliverables_raw, pipeline_tags, analysis_type_tags)

    # THEN the result should contain the data to be stored in Housekeeper
    snapshot.assert_match(mip_dna_files)


@mock.patch("cg.meta.store.base._determine_missing_tags")
def test_get_tags(mock_missing, dna_deliverables_raw: dict):
    """
    Tests get converted housekeeper tags
    """
    # GIVEN a MIP DNA analysis deliverables file, pipeline tags and corresponding analysis_tags
    mock_missing.return_value = False, []
    pipeline_tags = ["mip-dna"]
    analysis_type_tags = MIP_DNA_TAGS

    # WHEN getting the tags used to build the bundle
    for file_ in dna_deliverables_raw["files"]:
        deliverables_tag_map = (
            (file_["step"],) if file_["tag"] is None else (file_["step"], file_["tag"])
        )
        hk_tags = get_tags(file_, pipeline_tags, analysis_type_tags, deliverables_tag_map)
        # Then only analysis tags, pipeline tag and sample_id should be returned
        if file_["step"] == "samtools_subsample_mt":
            assert hk_tags == ["bam-mt", "mip-dna", "sample_id"]
        if file_["step"] == "gatk_baserecalibration":
            assert hk_tags == ["cram", "mip-dna", "sample_id"]


@mock.patch("cg.meta.store.base._determine_missing_tags")
def test_get_tags_for_index_file(mock_missing, dna_deliverables_raw: dict):
    """
    Tests get converted housekeeper tags for index file
    """
    # GIVEN a MIP DNA analysis deliverables file, pipeline tags and corresponding analysis_tags
    mock_missing.return_value = False, []
    pipeline_tags = ["mip-dna"]
    analysis_type_tags = MIP_DNA_TAGS

    # WHEN getting the tags used to build the bundle
    for file_ in dna_deliverables_raw["files"]:
        if file_["path_index"]:
            deliverables_tag_map = (
                (file_["step"],) if file_["tag"] is None else (file_["step"], file_["tag"])
            )
            hk_tags = get_tags(
                file_, pipeline_tags, analysis_type_tags, deliverables_tag_map, is_index=True
            )
            # Then only analysis tags, pipeline tag and sample_id should be returned
            if file_["step"] == "samtools_subsample_mt":
                assert hk_tags == ["bam-mt-index", "mip-dna", "sample_id"]
            if file_["step"] == "gatk_baserecalibration":
                assert hk_tags == ["cram-index", "mip-dna", "sample_id"]
