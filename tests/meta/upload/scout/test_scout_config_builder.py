"""Tests for the file handlers."""

import logging

from housekeeper.store.models import Version

from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.hk_tags import CaseTags
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.raredisease_config_builder import RarediseaseConfigBuilder
from cg.meta.upload.scout.rnafusion_config_builder import RnafusionConfigBuilder
from cg.store.models import Analysis
from cg.store.store import Store
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.madeline import MockMadelineAPI
from tests.mocks.mip_analysis_mock import MockMipAnalysis


def test_mip_config_builder(
    hk_version: Version,
    mip_dna_analysis: Analysis,
    lims_api: MockLimsAPI,
    mip_analysis_api: MockMipAnalysis,
    madeline_api: MockMadelineAPI,
    analysis_store: Store
):
    """Test MIP config builder class."""
    # GIVEN a MIP analysis

    # WHEN instantiating
    config_builder = MipConfigBuilder(
        hk_version_obj=hk_version,
        analysis_obj=mip_dna_analysis,
        lims_api=lims_api,
        mip_analysis_api=mip_analysis_api,
        madeline_api=madeline_api,
        status_db=analysis_store
    )

    # THEN assert that the correct case tags was used
    assert isinstance(config_builder.case_tags, CaseTags)


def test_balsamic_config_builder(
    hk_version: Version, balsamic_analysis_obj: Analysis, lims_api: MockLimsAPI, analysis_store: Store
):
    """Test Balsamic config builder class."""
    # GIVEN a balsamic file handler

    # WHEN instantiating
    file_handler = BalsamicConfigBuilder(
        hk_version_obj=hk_version, analysis_obj=balsamic_analysis_obj, lims_api=lims_api, status_db=analysis_store
    )

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, CaseTags)


def test_raredisease_config_builder(
    hk_version: Version,
    raredisease_analysis_obj: Analysis,
    lims_api: MockLimsAPI,
    raredisease_analysis_api: RarediseaseAnalysisAPI,
    madeline_api: MockMadelineAPI,
    analysis_store: Store
):
    """Test RAREDISEASE config builder class."""
    # GIVEN a RAREDISEASE file handler

    # WHEN instantiating
    file_handler = RarediseaseConfigBuilder(
        hk_version_obj=hk_version,
        analysis_obj=raredisease_analysis_obj,
        lims_api=lims_api,
        raredisease_analysis_api=raredisease_analysis_api,
        madeline_api=madeline_api,
        status_db=analysis_store
    )

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, CaseTags)


def test_rnafusion_config_builder(
    hk_version: Version,
    rnafusion_analysis_obj: Analysis,
    lims_api: MockLimsAPI,
    analysis_store: Store
):
    """Test RNAfusion config builder class."""
    # GIVEN a rnafusion file handler

    # WHEN instantiating
    file_handler = RnafusionConfigBuilder(
        hk_version_obj=hk_version, analysis_obj=rnafusion_analysis_obj, lims_api=lims_api, status_db=analysis_store
    )

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, CaseTags)


def test_include_synopsis(mip_config_builder: MipConfigBuilder):
    """Test include synopsis."""
    # GIVEN a config builder with some data

    # GIVEN a config without synopsis
    assert mip_config_builder.load_config.synopsis is None

    # WHEN including the synopsis
    load_config =mip_config_builder.build_load_config()

    # THEN assert that the synopsis was added
    assert load_config.synopsis


def test_include_phenotype_groups(mip_config_builder: MipConfigBuilder):
    """Test include phenotype groups."""
    # GIVEN a config builder with some data

    # GIVEN a config without a phenotype groups
    assert mip_config_builder.load_config.phenotype_groups is None

    # WHEN including the phenotype groups
    mip_config_builder.include_phenotype_groups(load_config=mip_config_builder.load_config)

    # THEN assert that the phenotype groups were added
    assert mip_config_builder.load_config.phenotype_groups is not None


def test_include_phenotype_terms(mip_config_builder: MipConfigBuilder):
    """Test include phenotype terms."""
    # GIVEN a config builder with some data

    # GIVEN a config without a phenotype terms
    assert mip_config_builder.load_config.phenotype_terms is None

    # WHEN including the phenotype terms
    mip_config_builder.include_phenotype_terms(load_config=mip_config_builder.load_config)

    # THEN assert that the phenotype terms were added
    assert mip_config_builder.load_config.phenotype_terms is not None


def test_include_alignment_file_individual(mip_config_builder: MipConfigBuilder, sample_id: str):
    """Test include alignment files."""
    # GIVEN a mip config builder with some information

    # WHEN building the scout load config
    load_config = mip_config_builder.build_load_config()

    # THEN assert that the alignment file was added to sample id
    file_found = False
    for sample in load_config.samples:
        if sample.sample_id == sample_id:
            assert sample.alignment_path is not None
            file_found = True
    assert file_found


def test_include_mip_case_files(mip_config_builder: MipConfigBuilder):
    """Test include MIP case files."""
    # GIVEN a Housekeeper version bundle with MIP analysis files
    # GIVEN a case load object
    # GIVEN a MIP file handler

    # WHEN including the case level files
    load_config = mip_config_builder.build_load_config()

    # THEN assert that the mandatory SNV VCF was added
    assert load_config.vcf_snv


def test_include_mip_sample_files(mip_config_builder: MipConfigBuilder, sample_id: str):
    """Test include MIP sample files."""
    # GIVEN a Housekeeper version bundle with MIP analysis files
    # GIVEN a case load object
    # GIVEN that there are no sample level mt_bam

    # GIVEN a MIP file handler

    # WHEN including the case level files
    load_config = mip_config_builder.build_load_config()

    # THEN assert that the mandatory SNV VCF was added
    file_found = False
    for sample in load_config.samples:
        if sample.sample_id == sample_id:
            assert sample.mt_bam is not None
            file_found = True
    assert file_found


def test_include_mip_sample_subject_id(
    mip_config_builder: MipConfigBuilder, sample_id: str, caplog
):
    """Test include MIP sample subject id."""
    # GIVEN subject_id on the sample
    caplog.set_level(level=logging.DEBUG)

    # WHEN building the config
    load_config = mip_config_builder.build_load_config()

    # THEN the subject_id was added to the scout sample
    subject_id_found = False
    for sample in load_config.samples:
        if sample.sample_id == sample_id:
            subject_id_found = True
            assert sample.subject_id is not None
    assert subject_id_found


def test_include_balsamic_case_files(balsamic_config_builder: BalsamicConfigBuilder):
    """Test include Balsamic case files."""
    # GIVEN a Housekeeper version bundle with balsamic analysis files
    # GIVEN a case load object

    # WHEN including the case level files
    balsamic_config_builder.build_load_config()

    # THEN assert that the mandatory snv vcf was added
    assert balsamic_config_builder.load_config.vcf_cancer


def test_include_balsamic_delivery_report(balsamic_config_builder: BalsamicConfigBuilder):
    """Test include Balsamic delivery report."""
    # GIVEN a Housekeeper version bundle with balsamic analysis files
    # GIVEN a case load object

    # WHEN including the case level files
    balsamic_config_builder.build_load_config()

    # THEN assert that the delivery_report exists
    assert balsamic_config_builder.load_config.delivery_report


def test_remove_chromosome_substring(mip_config_builder: MipConfigBuilder):
    """Test that parsing of file path."""

    # GIVEN files paths ending with
    file_path1 = "/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_X.png"
    file_path2 = "/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_12.png"

    # THEN calling extracting the generic path will remove numeric id and fuffix
    generic_path = "/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_"

    # THEN
    assert mip_config_builder.remove_chromosome_substring(file_path1) == generic_path
    assert mip_config_builder.remove_chromosome_substring(file_path2) == generic_path
