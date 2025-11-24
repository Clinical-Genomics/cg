"""Tests for the file handlers."""

import logging
from datetime import datetime
from unittest.mock import Mock

import pytest
from housekeeper.store.models import File, Version
from mock import create_autospec
from pytest_mock import MockerFixture

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims.api import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.constants import Priority, Workflow
from cg.constants.constants import SexOptions
from cg.constants.housekeeper_tags import AlignmentFileTag, NalloAnalysisTag
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.hk_tags import CaseTags
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.nallo_config_builder import NalloConfigBuilder
from cg.meta.upload.scout.raredisease_config_builder import RarediseaseConfigBuilder
from cg.meta.upload.scout.rnafusion_config_builder import RnafusionConfigBuilder
from cg.meta.workflow.nallo import NalloAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.orders.sample_base import StatusEnum
from cg.models.scout.scout_load_config import NalloLoadConfig, Reviewer, ScoutNalloIndividual
from cg.store.models import (
    Analysis,
    Application,
    ApplicationVersion,
    Case,
    CaseSample,
    Customer,
    Sample,
)
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.madeline import MockMadelineAPI
from tests.mocks.mip_analysis_mock import MockMipAnalysis


def test_mip_config_builder(
    lims_api: MockLimsAPI,
    mip_analysis_api: MockMipAnalysis,
    madeline_api: MockMadelineAPI,
):
    """Test MIP config builder class."""
    # GIVEN a MIP analysis

    # WHEN instantiating
    config_builder = MipConfigBuilder(
        lims_api=lims_api,
        mip_analysis_api=mip_analysis_api,
        madeline_api=madeline_api,
    )

    # THEN assert that the correct case tags was used
    assert isinstance(config_builder.case_tags, CaseTags)


def test_balsamic_config_builder(
    lims_api: MockLimsAPI,
):
    """Test Balsamic config builder class."""
    # GIVEN a balsamic file handler

    # WHEN instantiating
    file_handler = BalsamicConfigBuilder(
        lims_api=lims_api,
    )

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, CaseTags)


def test_raredisease_config_builder(
    lims_api: MockLimsAPI,
    raredisease_analysis_api: RarediseaseAnalysisAPI,
    madeline_api: MockMadelineAPI,
):
    """Test RAREDISEASE config builder class."""
    # GIVEN a RAREDISEASE file handler

    # WHEN instantiating
    file_handler = RarediseaseConfigBuilder(
        lims_api=lims_api,
        raredisease_analysis_api=raredisease_analysis_api,
        madeline_api=madeline_api,
    )

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, CaseTags)


def test_rnafusion_config_builder(
    rnafusion_analysis: Analysis,
    lims_api: MockLimsAPI,
):
    """Test RNAfusion config builder class."""
    # GIVEN a rnafusion file handler

    # WHEN instantiating
    file_handler = RnafusionConfigBuilder(
        lims_api=lims_api,
    )

    # THEN assert that the correct case tags was used
    assert isinstance(file_handler.case_tags, CaseTags)


def test_include_synopsis(
    mip_config_builder: MipConfigBuilder,
    mip_dna_analysis: Analysis,
    mip_dna_analysis_hk_version: Version,
):
    """Test include synopsis."""
    # GIVEN a config builder with some data

    # WHEN including the synopsis
    load_config = mip_config_builder.build_load_config(
        analysis=mip_dna_analysis, hk_version=mip_dna_analysis_hk_version
    )

    # THEN assert that the synopsis was added
    assert load_config.synopsis


def test_include_phenotype_groups(
    mip_config_builder: MipConfigBuilder,
    mip_dna_analysis: Analysis,
    mip_dna_analysis_hk_version: Version,
):
    """Test include phenotype groups."""
    # GIVEN a config builder with some data
    load_config = mip_config_builder.build_load_config(
        analysis=mip_dna_analysis, hk_version=mip_dna_analysis_hk_version
    )

    # WHEN including the phenotype groups
    mip_config_builder.include_phenotype_groups(load_config, analysis=mip_dna_analysis)

    # THEN assert that the phenotype groups were added
    assert load_config.phenotype_groups is not None


def test_include_phenotype_terms(
    mip_config_builder: MipConfigBuilder,
    mip_dna_analysis: Analysis,
    mip_dna_analysis_hk_version: Version,
):
    """Test include phenotype terms."""
    # GIVEN a config builder with some data

    load_config = mip_config_builder.build_load_config(
        analysis=mip_dna_analysis, hk_version=mip_dna_analysis_hk_version
    )

    # WHEN including the phenotype terms
    mip_config_builder.include_phenotype_terms(load_config, analysis=mip_dna_analysis)

    # THEN assert that the phenotype terms were added
    assert load_config.phenotype_terms is not None


def test_include_alignment_file_individual(
    mip_config_builder: MipConfigBuilder,
    sample_id: str,
    mip_dna_analysis: Analysis,
    mip_dna_analysis_hk_version: Version,
):
    """Test include alignment files."""
    # GIVEN a mip config builder with some information

    # WHEN building the scout load config
    load_config = mip_config_builder.build_load_config(
        analysis=mip_dna_analysis, hk_version=mip_dna_analysis_hk_version
    )

    # THEN assert that the alignment file was added to sample id
    file_found = False
    for sample in load_config.samples:
        if sample.sample_id == sample_id:
            assert sample.alignment_path is not None
            file_found = True
    assert file_found


def test_include_mip_case_files(
    mip_config_builder: MipConfigBuilder,
    mip_dna_analysis: Analysis,
    mip_dna_analysis_hk_version: Version,
):
    """Test include MIP case files."""
    # GIVEN a Housekeeper version bundle with MIP analysis files
    # GIVEN a case load object
    # GIVEN a MIP file handler

    # WHEN including the case level files
    load_config = mip_config_builder.build_load_config(
        analysis=mip_dna_analysis, hk_version=mip_dna_analysis_hk_version
    )

    # THEN assert that the mandatory SNV VCF was added
    assert load_config.vcf_snv


def test_include_mip_sample_files(
    mip_config_builder: MipConfigBuilder,
    sample_id: str,
    mip_dna_analysis: Analysis,
    mip_dna_analysis_hk_version: Version,
):
    """Test include MIP sample files."""
    # GIVEN a Housekeeper version bundle with MIP analysis files
    # GIVEN a case load object
    # GIVEN that there are no sample level mt_bam

    # GIVEN a MIP file handler

    # WHEN including the case level files
    load_config = mip_config_builder.build_load_config(
        analysis=mip_dna_analysis, hk_version=mip_dna_analysis_hk_version
    )

    # THEN assert that the mandatory SNV VCF was added
    file_found = False
    for sample in load_config.samples:
        if sample.sample_id == sample_id:
            assert sample.mt_bam is not None
            file_found = True
    assert file_found


def test_include_mip_sample_subject_id(
    mip_config_builder: MipConfigBuilder,
    sample_id: str,
    mip_dna_analysis: Analysis,
    mip_dna_analysis_hk_version: Version,
    caplog,
):
    """Test include MIP sample subject id."""
    # GIVEN subject_id on the sample
    caplog.set_level(level=logging.DEBUG)

    # WHEN building the config
    load_config = mip_config_builder.build_load_config(
        analysis=mip_dna_analysis, hk_version=mip_dna_analysis_hk_version
    )

    # THEN the subject_id was added to the scout sample
    subject_id_found = False
    for sample in load_config.samples:
        if sample.sample_id == sample_id:
            subject_id_found = True
            assert sample.subject_id is not None
    assert subject_id_found


def test_include_balsamic_case_files(
    balsamic_config_builder: BalsamicConfigBuilder,
    balsamic_analysis: Analysis,
    balsamic_analysis_hk_version: Version,
):
    """Test include Balsamic case files."""
    # GIVEN a Housekeeper version bundle with balsamic analysis files
    # GIVEN a case load object

    # WHEN including the case level files
    load_config = balsamic_config_builder.build_load_config(
        analysis=balsamic_analysis, hk_version=balsamic_analysis_hk_version
    )

    # THEN assert that the mandatory snv vcf was added
    assert load_config.vcf_cancer


def test_include_balsamic_delivery_report(
    balsamic_config_builder: BalsamicConfigBuilder,
    balsamic_analysis: Analysis,
    balsamic_analysis_hk_version: Version,
):
    """Test include Balsamic delivery report."""
    # GIVEN a Housekeeper version bundle with balsamic analysis files
    # GIVEN a case load object

    # WHEN including the case level files
    load_config = balsamic_config_builder.build_load_config(
        analysis=balsamic_analysis, hk_version=balsamic_analysis_hk_version
    )

    # THEN assert that the delivery_report exists
    assert load_config.delivery_report


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


@pytest.mark.freeze_time
def test_nallo_config_builder(mocker: MockerFixture):
    lims_api = create_autospec(LimsAPI)
    lims_api.sample = Mock(return_value={"tissue_type": "blood"})

    # GIVEN a Nallo config builder
    nallo_config_builder = NalloConfigBuilder(
        nallo_analysis_api=create_autospec(NalloAnalysisAPI),
        lims_api=lims_api,
        madeline_api=create_autospec(MadelineAPI),
    )

    # Case Files
    delivery_report: File = create_autospec(File, full_path="delivery_report.yaml")
    multiqc: File = create_autospec(File, full_path="multiqc.html")
    peddy_check: File = create_autospec(File, full_path="check.peddy")
    peddy_ped: File = create_autospec(File, full_path="ped.peddy")
    peddy_sex: File = create_autospec(File, full_path="sex.peddy")
    vcf_snv_research: File = create_autospec(File, full_path="snv_research.vcf")
    vcf_snv: File = create_autospec(File, full_path="snv_clinical.vcf")
    vcf_sv: File = create_autospec(File, full_path="sv.vcf")
    vcf_sv_research: File = create_autospec(File, full_path="sv_research.vcf")
    vcf_snv_research: File = create_autospec(File, full_path="snv_research.vcf")
    vcf_str: File = create_autospec(File, full_path="str.vcf")

    # Sample files
    alignment_path: File = create_autospec(File, full_path="haplo.bam")
    d4_file: File = create_autospec(File, full_path="coverage.d4")
    tiddit_coverage_wig: File = create_autospec(File, full_path="bigwig_hifi.cnv")
    paraphase_alignment_path: File = create_autospec(File, full_path="paraphase.bam")
    phase_blocks: File = create_autospec(File, full_path="phase_blocks.gtf")
    minor_allele_frequency_wig: File = create_autospec(
        File, full_path="minor_allele_frequency.bigwig"
    )

    # GIVEN files exist in Housekeeper for each set of NALLO_CASE_TAG and NALLO_SAMPLE_TAG
    def mock_get_file_from_version(version: Version, tags: set[str]) -> File | None:
        # Case tags
        if tags == {"delivery-report"}:
            return delivery_report
        elif tags == {"multiqc-html"}:
            return multiqc
        elif tags == {"ped-check", "peddy"}:
            return peddy_check
        elif tags == {"ped", "peddy"}:
            return peddy_ped
        elif tags == {"sex-check", "peddy"}:
            return peddy_sex
        elif tags == {"vcf-snv-research"}:
            return vcf_snv_research
        elif tags == {"vcf-snv-clinical"}:
            return vcf_snv
        elif tags == {"vcf-sv-research"}:
            return vcf_sv_research
        elif tags == {"vcf-sv-clinical"}:
            return vcf_sv
        elif tags == {"vcf-str"}:
            return vcf_str
        # Sample tags
        elif tags == {AlignmentFileTag.BAM, "haplotags", "sample_id"}:
            return alignment_path
        elif tags == {"coverage", "d4", "sample_id"}:
            return d4_file
        elif tags == {"hificnv", "bigwig", "sample_id"}:
            return tiddit_coverage_wig
        elif tags == {AlignmentFileTag.BAM, NalloAnalysisTag.PARAPHASE, "sample_id"}:
            return paraphase_alignment_path
        elif tags == {"whatshap", "gtf", "sample_id"}:
            return phase_blocks
        elif tags == {"repeats", "spanning", "bam", "sample_id"}:
            return create_autospec(File, full_path="repeats_spanning.bam")
        elif tags == {"repeats", "spanning", "bam-index", "sample_id"}:
            return create_autospec(File, full_path="repeats_spanning.index")
        elif tags == {"repeats", "sorted", "vcf", "sample_id"}:
            return create_autospec(File, full_path="repeats_sorted.vcf")
        elif tags == {"trgt", "variant-catalog"}:
            return create_autospec(File, full_path="variant_catalog.trgt")
        elif tags == {"hificnv", "bigwig", "maf", "sample_id"}:
            return minor_allele_frequency_wig
        raise Exception

    mocker.patch.object(
        HousekeeperAPI, "get_file_from_version", side_effect=mock_get_file_from_version
    )
    version = create_autospec(Version)

    # GIVEN an analysis tied to a case which is in turn tied to a sample and a customer
    application: Application = create_autospec(
        Application, analysis_type=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING.value
    )
    sample: Sample = create_autospec(
        Sample,
        application_version=create_autospec(ApplicationVersion, application=application),
        internal_id="sample_id",
        sex=SexOptions.FEMALE,
        subject_id="sample_subject",
    )
    sample.name = "sample_name"
    case_sample: CaseSample = create_autospec(
        CaseSample, father=None, mother=None, sample=sample, status=StatusEnum.affected
    )
    customer: Customer = create_autospec(Customer, internal_id="cust000")
    case: Case = create_autospec(
        Case,
        customer=customer,
        data_analysis=Workflow.NALLO,
        internal_id="case_id",
        links=[case_sample],
        priority=Priority.standard,
        synopsis=None,
    )
    case_sample.case = case
    case.name = "case_name"
    analysis: Analysis = create_autospec(Analysis, case=case, completed_at=datetime.now())

    # WHEN building the Nallo Scout load config
    load_config: NalloLoadConfig = nallo_config_builder.build_load_config(
        hk_version=version, analysis=analysis
    )

    expected_load_config = NalloLoadConfig(
        owner=customer.internal_id,
        family=case.internal_id,
        family_name=case.name,
        status=None,
        synopsis=None,
        phenotype_terms=None,
        phenotype_groups=None,
        gene_panels=[],
        default_gene_panels=[],
        cohorts=[],
        human_genome_build="38",
        rank_model_version="1.0",
        rank_score_threshold=8,
        sv_rank_model_version="1.0",
        analysis_date=datetime.now(),
        samples=[
            ScoutNalloIndividual(
                alignment_path=alignment_path.full_path,
                rna_alignment_path=None,
                analysis_type="wgs",
                capture_kit=None,
                confirmed_parent=None,
                confirmed_sex=None,
                father="0",
                mother="0",
                phenotype=case_sample.status,
                sample_id=sample.internal_id,
                sample_name=sample.name,
                sex=sample.sex,
                subject_id=sample.subject_id,
                tissue_type="unknown",
                assembly_alignment_path=None,
                d4_file=d4_file.full_path,
                minor_allele_frequency_wig=minor_allele_frequency_wig.full_path,
                mt_bam=alignment_path.full_path,
                paraphase_alignment_path=paraphase_alignment_path.full_path,
                phase_blocks=phase_blocks.full_path,
                reviewer=Reviewer(
                    alignment="repeats_spanning.bam",
                    alignment_index="repeats_spanning.index",
                    vcf="repeats_sorted.vcf",
                    catalog="variant_catalog.trgt",
                    trgt=True,
                ),
                tiddit_coverage_wig="bigwig_hifi.cnv",
            )
        ],
        customer_images=None,
        delivery_report=delivery_report.full_path,
        coverage_qc_report=None,
        cnv_report=None,
        multiqc=multiqc.full_path,
        track="rare",
        madeline=None,
        peddy_check=peddy_check.full_path,
        peddy_ped=peddy_ped.full_path,
        peddy_sex=peddy_sex.full_path,
        somalier_samples=None,
        somalier_pairs=None,
        vcf_snv=vcf_snv.full_path,
        vcf_snv_research=vcf_snv_research.full_path,
        vcf_sv=vcf_sv.full_path,
        vcf_sv_research=vcf_sv_research.full_path,
        vcf_str=vcf_str.full_path,
    )

    assert load_config == expected_load_config
