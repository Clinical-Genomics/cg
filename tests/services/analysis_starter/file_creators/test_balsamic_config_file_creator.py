from typing import cast
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

import cg.services.analysis_starter.configurator.file_creators.balsamic_config as creator
from cg.apps.lims.api import LimsAPI
from cg.constants import SexOptions
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.store.models import BedVersion, Case, Sample
from cg.store.store import Store


@pytest.fixture
def expected_tgs_normal_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--pon-cnn {cg_balsamic_config.pon_path} "  # TODO double check this
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_normal"
    )


@pytest.fixture
def expected_tgs_paired_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "  # TODO are there 2 versions of this?
        f"--normal-sample-name sample_normal "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--soft-filter-normal "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_tumour "
    )


@pytest.fixture
def expected_tgs_tumour_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--pon-cnn {cg_balsamic_config.pon_path} "  # TODO add a check for with and without pon
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_1"
    )


@pytest.fixture
def expected_wes_normal_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--exome "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--pon-cnn {cg_balsamic_config.pon_path} "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_normal"
    )


@pytest.fixture
def expected_wes_paired_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--exome "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--normal-sample-name sample_normal "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--soft-filter-normal "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_tumour"
    )


@pytest.fixture
def expected_wes_tumour_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--exome "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--pon-cnn {cg_balsamic_config.pon_path} "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_1"
    )


@pytest.fixture
def expected_wgs_tumour_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--artefact-sv-observations {cg_balsamic_config.loqusdb_artefact_sv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-interval {cg_balsamic_config.genome_interval_path} "
        f"--genome-version hg19 "
        f"--gens-coverage-pon {cg_balsamic_config.gens_coverage_female_path} "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_1"
    )


@pytest.fixture
def expected_wgs_paired_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--artefact-sv-observations {cg_balsamic_config.loqusdb_artefact_sv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-interval {cg_balsamic_config.genome_interval_path} "
        f"--genome-version hg19 "
        f"--gens-coverage-pon {cg_balsamic_config.gens_coverage_female_path} "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--normal-sample-name sample_normal "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_tumour"
    )


def test_create_tgs_normal_only(
    cg_balsamic_config: BalsamicConfig, expected_tgs_normal_only_command: str, mocker: MockerFixture
):
    # GIVEN a case with one normal TGS sample
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
        sex=SexOptions.FEMALE,
    )
    tgs_normal_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )
    store: Store = create_autospec(Store)

    store.get_case_by_internal_id = Mock(return_value=tgs_normal_only_case)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_tgs_normal_only_command, check=True, shell=True, stderr=-1, stdout=-1
    )


def test_create_wgs_paired(
    cg_balsamic_config: BalsamicConfig, expected_wgs_paired_command: str, mocker: MockerFixture
):
    # GIVEN a case with one tumor and one normal WGS samples
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    normal_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )
    wgs_paired_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample, normal_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id = Mock(return_value=wgs_paired_case)

    # GIVEN a Lims API

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wgs_paired_command, check=True, shell=True, stderr=-1, stdout=-1
    )


def test_create_wgs_tumor_only(
    cg_balsamic_config: BalsamicConfig, expected_wgs_tumour_only_command: str, mocker: MockerFixture
):
    # GIVEN a case with one tumor WGS sample
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_1",
        is_tumour=True,
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
        sex=SexOptions.FEMALE,
    )
    wgs_tumor_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id = Mock(return_value=wgs_tumor_only_case)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wgs_tumour_only_command, check=True, shell=True, stderr=-1, stdout=-1
    )


def test_create_wes_paired(
    cg_balsamic_config: BalsamicConfig, expected_wes_paired_command: str, mocker: MockerFixture
):
    # GIVEN a case with one tumor and one normal WES samples
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
    )
    normal_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
    )
    wes_paired_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample, normal_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id = Mock(return_value=wes_paired_case)
    store.get_bed_version_by_short_name = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.capture_kit = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the bed version should have been fetched using the LIMS capture kit
    cast(Mock, store.get_bed_version_by_short_name).assert_called_once_with("bed_short_name")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wes_paired_command, check=True, shell=True, stderr=-1, stdout=-1
    )
