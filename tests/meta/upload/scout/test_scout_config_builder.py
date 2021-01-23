"""Tests for the file handlers"""
from typing import Optional

from housekeeper.store import models as hk_models

from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_load_config import (
    BalsamicLoadConfig,
    MipLoadConfig,
    ScoutLoadConfig,
    ScoutMipIndividual,
)
from cg.store import models
from tests.mocks.madeline import MockMadelineAPI
from .conftest import MockLims, MockAnalysis


def test_mip_config_builder(
    hk_version_obj: hk_models.Version,
    mip_analysis_obj: models.Analysis,
    lims_api: MockLims,
    mip_analysis_api: MockAnalysis,
    madeline_api: MockMadelineAPI,
):
    # GIVEN a mip file handler

    # WHEN instantiating
    file_handler = MipConfigBuilder(
        hk_version_obj=hk_version_obj,
        analysis_obj=mip_analysis_obj,
        lims_api=lims_api,
        mip_analysis_api=mip_analysis_api,
        madeline_api=madeline_api,
    )

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, CaseTags)


def test_balsamic_config_builder(
    hk_version_obj: hk_models.Version, balsamic_analysis_obj: models.Analysis, lims_api: MockLims
):
    # GIVEN a balsamic file handler

    # WHEN instantiating
    file_handler = BalsamicConfigBuilder(
        hk_version_obj=hk_version_obj, analysis_obj=balsamic_analysis_obj, lims_api=lims_api
    )

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, CaseTags)


def test_include_delivery_report(mip_analysis_hk_version: hk_models.Version):
    # GIVEN a housekeeper version object with a delivery report
    file_obj: hk_models.File
    report: Optional[hk_models.File] = None
    for file_obj in mip_analysis_hk_version.files:
        tag: hk_models.Tag
        tags = {tag.name for tag in file_obj.tags}
        if "delivery-report" in tags:
            report = file_obj
    assert report
    # GIVEN a mip file handler
    file_handler = MipConfigBuilder(hk_version_obj=mip_analysis_hk_version)

    # GIVEN a scout load case without a delivery report
    load_case = ScoutLoadConfig()
    assert load_case.delivery_report is None

    # WHEN including the delivery report
    file_handler.include_delivery_report(case=load_case)

    # THEN assert that the delivery report was added
    assert load_case.delivery_report == report.full_path


def test_include_alignment_file_individual(
    mip_analysis_hk_version: hk_models.Version, sample_id: str
):
    # GIVEN a housekeeper version object with a cram file
    file_obj: hk_models.File
    alignment_file: Optional[hk_models.File] = None
    for file_obj in mip_analysis_hk_version.files:
        tag: hk_models.Tag
        tags = {tag.name for tag in file_obj.tags}
        if "cram" in tags:
            alignment_file = file_obj
    assert alignment_file
    # GIVEN a mip file handler
    file_handler = MipConfigBuilder(hk_version_obj=mip_analysis_hk_version)

    # GIVEN a scout load case without a delivery report
    mip_individual = ScoutMipIndividual(sample_id=sample_id)
    assert mip_individual.alignment_path is None

    # WHEN including the delivery report
    file_handler.include_sample_alignment_file(sample=mip_individual)

    # THEN assert that the delivery report was added
    assert mip_individual.alignment_path == alignment_file.full_path


def test_include_mip_case_files(mip_analysis_hk_version: hk_models.Version):
    # GIVEN a housekeeper version bundle with some mip analysis files
    # GIVEN a case load object
    load_case = MipLoadConfig()
    # GIVEN a mip file handler
    file_handler = MipConfigBuilder(hk_version_obj=mip_analysis_hk_version)

    # WHEN including the case level files
    file_handler.include_case_files(load_config=load_case)

    # THEN assert that the mandatory snv vcf was added
    assert load_case.vcf_snv


def test_include_mip_sample_files(mip_analysis_hk_version: hk_models.Version, sample_id: str):
    # GIVEN a housekeeper version bundle with some mip analysis files
    # GIVEN a case load object
    mip_sample = ScoutMipIndividual(sample_id=sample_id)
    # GIVEN that there are no sample level mt_bam
    mip_sample.mt_bam is None
    # GIVEN a mip file handler
    file_handler = MipConfigBuilder(hk_version_obj=mip_analysis_hk_version)

    # WHEN including the case level files
    file_handler.include_sample_files(sample=mip_sample)

    # THEN assert that the mandatory snv vcf was added
    assert mip_sample.mt_bam is not None


def test_include_balsamic_case_files(balsamic_analysis_hk_version: hk_models.Version):
    # GIVEN a housekeeper version bundle with some balsamic analysis files
    # GIVEN a case load object
    load_case = BalsamicLoadConfig()
    # GIVEN a balsamic file handler
    file_handler = BalsamicConfigBuilder(hk_version_obj=balsamic_analysis_hk_version)

    # WHEN including the case level files
    file_handler.include_case_files(load_config=load_case)

    # THEN assert that the mandatory snv vcf was added
    assert load_case.vcf_cancer


def test_extract_generic_filepath(hk_version_obj: hk_models.Version):
    """Test that parsing of file path"""
    file_handler = MipConfigBuilder(hk_version_obj)

    # GIVEN files paths ending with
    file_path1 = "/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_X.png"
    file_path2 = "/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_12.png"

    # THEN calling extracting the generic path will remove numeric id and fuffix
    generic_path = "/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_"

    # THEN
    assert file_handler.extract_generic_filepath(file_path1) == generic_path
    assert file_handler.extract_generic_filepath(file_path2) == generic_path
