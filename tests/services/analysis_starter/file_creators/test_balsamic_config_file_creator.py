from pathlib import Path
from typing import cast
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

import cg.services.analysis_starter.configurator.file_creators.balsamic_config as creator
from cg.apps.lims.api import LimsAPI
from cg.constants import SexOptions
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.exc import CaseNotFoundError, LimsDataError
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
        f"--tumor-sample-name sample_tumour"
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
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_tumour"
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
    store.get_case_by_internal_id_strict = Mock(return_value=tgs_normal_only_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_tgs_normal_only_command, check=True, shell=True, stderr=-1, stdout=-1
    )


def test_create_tgs_paired(
    cg_balsamic_config: BalsamicConfig, expected_tgs_paired_command: str, mocker: MockerFixture
):
    # GIVEN a case with one tumor and one normal WGS samples
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    normal_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    tgs_paired_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample, normal_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=tgs_paired_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_tgs_paired_command, check=True, shell=True, stderr=-1, stdout=-1
    )


def test_create_tgs_tumour_only(
    cg_balsamic_config: BalsamicConfig, expected_tgs_tumour_only_command: str, mocker: MockerFixture
):
    # GIVEN a case with one tumor TGS samples
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    tgs_tumour_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=tgs_tumour_only_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_tgs_tumour_only_command, check=True, shell=True, stderr=-1, stdout=-1
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
    store.get_case_by_internal_id_strict = Mock(return_value=wgs_paired_case)

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
    store.get_case_by_internal_id_strict = Mock(return_value=wgs_tumor_only_case)

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


def test_create_wes_normal_only(
    cg_balsamic_config: BalsamicConfig, expected_wes_normal_only_command: str, mocker: MockerFixture
):
    # GIVEN a case with one normal WES sample
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        sex=SexOptions.FEMALE,
    )
    wes_normal_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=wes_normal_only_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wes_normal_only_command, check=True, shell=True, stderr=-1, stdout=-1
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
    store.get_case_by_internal_id_strict = Mock(return_value=wes_paired_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the bed version should have been fetched using the LIMS capture kit
    cast(Mock, store.get_bed_version_by_short_name_strict).assert_called_once_with("bed_short_name")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wes_paired_command, check=True, shell=True, stderr=-1, stdout=-1
    )


def test_create_wes_tumour_only(
    cg_balsamic_config: BalsamicConfig, expected_wes_tumour_only_command: str, mocker: MockerFixture
):
    # GIVEN a case with one tumor WES sample
    sample: Sample = create_autospec(
        Sample,
        internal_id="sample_1",
        is_tumour=True,
        prep_category=SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING,
        sex=SexOptions.FEMALE,
    )
    wes_tumor_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=wes_tumor_only_case)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a Lims API
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(return_value="bed_short_name")

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    # THEN the bed version should have been fetched using the LIMS capture kit
    cast(Mock, store.get_bed_version_by_short_name_strict).assert_called_once_with("bed_short_name")

    # THEN the expected command is called
    mock_runner.assert_called_once_with(
        args=expected_wes_tumour_only_command, check=True, shell=True, stderr=-1, stdout=-1
    )


def test_create_no_case_found(cg_balsamic_config: BalsamicConfig):
    # GIVEN a store without cases
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=None, side_effect=CaseNotFoundError)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # WHEN creating a config file for a non-existing case
    # THEN a CaseNotFoundError is raised
    with pytest.raises(CaseNotFoundError):
        config_file_creator.create(case_id="non_existing_case")


def test_create_no_capture_kit_in_lims(cg_balsamic_config: BalsamicConfig):
    # GIVEN a store with a TGS Balsamic case
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
    )
    case_without_capture_kit: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id_strict = Mock(return_value=case_without_capture_kit)
    store.get_bed_version_by_short_name_strict = Mock(
        return_value=create_autospec(BedVersion, filename="bed_version.bed")
    )

    # GIVEN a LIMS API without a capture kit for the given case
    lims_api: LimsAPI = create_autospec(LimsAPI)
    lims_api.get_capture_kit_strict = Mock(side_effect=LimsDataError)

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=lims_api, cg_balsamic_config=cg_balsamic_config
    )

    # WHEN creating the config file for the case
    # THEN a LimsDataError error is raised
    with pytest.raises(LimsDataError):
        config_file_creator.create(case_id="case_1")


def test_get_pon_file(cg_balsamic_config: BalsamicConfig, tmp_path: Path):
    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=create_autospec(Store), lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )
    config_file_creator.pon_directory = tmp_path

    # GIVEN a bed file
    panel_name = "GMS_duck"
    bed_file = Path(config_file_creator.bed_directory, f"{panel_name}.bed")

    # GIVEN two matching PON files
    old_pon_path = Path(tmp_path, f"{panel_name}_CNVkit_PON_reference_v1.cnn")
    new_pon_path = Path(tmp_path, f"{panel_name}_CNVkit_PON_reference_v2.cnn")
    for pon_path in [old_pon_path, new_pon_path]:
        pon_path.touch()

    # WHEN getting the pon path
    pon_path: Path | None = config_file_creator._get_pon_file(bed_file)

    # THEN the returned path should be the latest version
    assert pon_path == new_pon_path


def test_get_pon_file_no_files(cg_balsamic_config: BalsamicConfig, tmp_path: Path):
    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=create_autospec(Store), lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )
    config_file_creator.pon_directory = tmp_path

    # GIVEN a bed file with no matching PON files
    panel_name = "GMS_duck"
    bed_file = Path(config_file_creator.bed_directory, f"{panel_name}.bed")

    # WHEN getting the pon path
    pon_file: Path | None = config_file_creator._get_pon_file(bed_file)

    # THEN None should be returned
    assert pon_file is None


def test_get_pon_file_no_matching_files(cg_balsamic_config: BalsamicConfig, tmp_path: Path):
    """Test that None is returned when no matching PON files are found."""
    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=create_autospec(Store), lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )
    config_file_creator.pon_directory = tmp_path

    # GIVEN a bed file with no matching PON files
    panel_name = "GMS_duck"
    bed_file = Path(config_file_creator.bed_directory, f"{panel_name}.bed")

    # GIVEN that there are files in the directory but none match the expected pattern
    (tmp_path / "some_other_file.txt").touch()

    # WHEN getting the pon path
    pon_file: Path | None = config_file_creator._get_pon_file(bed_file)

    # THEN None should be returned
    assert pon_file is None


@pytest.mark.parametrize(
    "sex, expected_file",
    [
        (SexOptions.FEMALE, "coverage_female.txt"),
        (SexOptions.MALE, "coverage_male.txt"),
        (SexOptions.UNKNOWN, "coverage_male.txt"),
    ],
    ids=["female", "male", "unknown"],
)
def test_get_gens_coverage_pon(
    cg_balsamic_config: BalsamicConfig, sex: SexOptions, expected_file: str
):
    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=Mock(), lims_api=Mock(), cg_balsamic_config=cg_balsamic_config
    )

    # WHEN getting the gens coverage file
    gens_pon_file: Path = config_file_creator._get_gens_coverage_pon_file(sex)

    # THEN the file is the expected
    assert gens_pon_file.name == expected_file
