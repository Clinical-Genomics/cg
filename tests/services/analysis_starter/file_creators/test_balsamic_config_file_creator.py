from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

import cg.services.analysis_starter.configurator.file_creators.balsamic_config as creator
from cg.constants import SexOptions
from cg.models.cg_config import BalsamicConfig
from cg.services.analysis_starter.configurator.file_creators.balsamic_config import (
    BalsamicConfigFileCreator,
)
from cg.store.models import Application, ApplicationVersion, Case, Sample
from cg.store.store import Store


@pytest.fixture
def expected_wgs_paired_command(balsamic_config: BalsamicConfig) -> str:
    return (
        f"{balsamic_config.conda_binary} "
        f"run --name {balsamic_config.conda_env} "
        f"{balsamic_config.binary_path} config case "
        f"--analysis-dir {balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--balsamic-cache {balsamic_config.balsamic_cache} "
        f"--cadd-annotations {balsamic_config.cadd_path} "
        f"--artefact-snv-observations {balsamic_config.loqusdb_artefact_snv} "
        f"--artefact-sv-observations {balsamic_config.loqusdb_artefact_sv} "
        f"--cancer-germline-snv-observations {balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-interval {balsamic_config.genome_interval_path} "
        f"--genome-version hg19 "
        f"--gens-coverage-pon {balsamic_config.gens_coverage_female_path} "
        f"--gnomad-min-af5 {balsamic_config.gnomad_af5_path} "
        f"--normal-sample-name sample_normal "
        f"--sentieon-install-dir {balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {balsamic_config.swegen_snv} "
        f"--swegen-sv {balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_tumour"
    )


def test_create_wgs_paired(
    balsamic_config: BalsamicConfig, expected_wgs_paired_command: str, mocker: MockerFixture
):
    # GIVEN a case with one tumor and one normal WGS samples
    application: Application = create_autospec(Application, prep_category="wgs")
    application_version: ApplicationVersion = create_autospec(
        ApplicationVersion, application=application
    )
    tumour_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_tumour",
        is_tumour=True,
        sex=SexOptions.FEMALE,
        application_version=application_version,
    )
    normal_sample: Sample = create_autospec(
        Sample,
        internal_id="sample_normal",
        is_tumour=False,
        sex=SexOptions.FEMALE,
        application_version=application_version,
    )
    wgs_tumor_only_case: Case = create_autospec(
        Case, data_analysis="balsamic", internal_id="case_1", samples=[tumour_sample, normal_sample]
    )
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id = Mock(return_value=wgs_tumor_only_case)

    # GIVEN a Lims API

    # GIVEN a BalsamicConfigFileCreator
    config_file_creator = BalsamicConfigFileCreator(
        status_db=store, lims_api=Mock(), cg_balsamic_config=balsamic_config
    )

    # GIVEN that the subprocess exits successfully
    mock_runner = mocker.patch.object(creator.subprocess, "run")

    # WHEN creating the config file
    config_file_creator.create(case_id="case_1")

    mock_runner.assert_called_once_with(
        args=expected_wgs_paired_command, check=True, shell=True, stderr=-1, stdout=-1
    )

    # # THEN the correct normal sample name should be set
    # assert cli_input.normal_sample_name is None
    #
    # # THEN the correct gens_coverage_pon should be chosen (Female)
    # assert cli_input.gens_coverage_pon == balsamic_configurator.gens_coverage_female_path
    #
    # # THEN fields not relevant for WGS analyses should be set to their default values
    # for field in PANEL_ONLY_FIELDS:
    #     assert getattr(cli_input, field) == BalsamicConfigInput.model_fields[field].default
